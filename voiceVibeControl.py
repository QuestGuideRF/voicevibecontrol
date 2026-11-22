import pygame
import numpy as np
import threading
import time
import sys
import sounddevice as sd
class SimpleAudioVibrateController :
    def __init__ (self ):
        pygame .init ()
        pygame .joystick .init ()
        self .sensitivity =1.5
        self .smoothing =0.7
        self .running =True
        self .current_intensity =0.0
        if pygame .joystick .get_count ()==0 :
            return
        self .joystick =pygame .joystick .Joystick (0 )
        self .joystick .init ()
        try :
            self .joystick .rumble (0 ,0 ,100 )
            self .vibration_supported =True
        except :
            self .vibration_supported =False
            return
        self .sample_rate =44100
        self .block_duration =50
        self .blocksize =int (self .sample_rate *self .block_duration /1000 )
        self .mode ="volume"
        self .button_states ={}
        self .show_levels =False
        self .setup_audio_stream ()
    def setup_audio_stream (self ):
        try :
            devices =sd .query_devices ()
            loopback_device =None
            for i ,device in enumerate (devices ):
                if device ['max_input_channels']>0 :
                    device_name =device ['name'].lower ()
                    if any (keyword in device_name for keyword in
                    ['стерео микс','что ты слышишь','отмахнуться','loopback']):
                        loopback_device =i
                        break
            if loopback_device is None :
                loopback_device =sd .default .device [0 ]
            else :
                pass
            self .audio_stream =sd .InputStream (
            device =loopback_device ,
            channels =1 ,
            samplerate =self .sample_rate ,
            blocksize =self .blocksize ,
            callback =self .audio_callback
            )
        except Exception as e :
            try :
                self .audio_stream =sd .InputStream (
                channels =1 ,
                samplerate =self .sample_rate ,
                blocksize =self .blocksize ,
                callback =self .audio_callback
                )
            except Exception as e2 :
                self .audio_stream =None
                return
    def audio_callback (self ,indata ,frames ,time ,status ):
        audio_data =indata [:,0 ]if len (indata .shape )>1 else indata
        if self .mode =="volume":
            rms =np .sqrt (np .mean (audio_data **2 ))
            intensity =min (rms *self .sensitivity *10 ,1.0 )
        else :
            fft =np .fft .fft (audio_data )
            freqs =np .fft .fftfreq (len (fft ),1 /self .sample_rate )
            bass_range =(np .abs (freqs )>=20 )&(np .abs (freqs )<=250 )
            bass_power =np .sum (np .abs (fft [bass_range ]))
            intensity =min (bass_power /1000 *self .sensitivity ,1.0 )
        self .current_intensity =(
        self .smoothing *self .current_intensity +
        (1 -self .smoothing )*intensity
        )
        self .apply_vibration (self .current_intensity )
    def apply_vibration (self ,intensity ):
        if not self .vibration_supported :
            return
        if intensity >0.05 :
            vibration_strength =max (0.1 ,min (intensity ,1.0 ))
            if self .mode =="bass":
                left_motor =vibration_strength
                right_motor =vibration_strength *0.3
            else :
                left_motor =vibration_strength *0.8
                right_motor =vibration_strength *0.8
            self .joystick .rumble (left_motor ,right_motor ,50 )
            if self .show_levels :
                bar_length =int (intensity *30 )
                bar ="█"*bar_length +"░"*(30 -bar_length )
                mode_icon ="🔊"if self .mode =="volume"else "🎵"
        else :
            self .joystick .rumble (0 ,0 ,50 )
            if self .show_levels :
                mode_icon ="🔊"if self .mode =="volume"else "🎵"
    def handle_button_press (self ,button ,pressed ):
        if button not in self .button_states :
            self .button_states [button ]=False
        if pressed and not self .button_states [button ]:
            if button ==0 :
                self .mode ="bass"if self .mode =="volume"else "volume"
                mode_name ="🎵 Басы"if self .mode =="bass"else "🔊 Громкость"
            elif button ==3 :
                self .sensitivity =min (self .sensitivity +0.3 ,5.0 )
            elif button ==1 :
                self .sensitivity =max (self .sensitivity -0.3 ,0.2 )
            elif button ==2 :
                self .show_levels =not self .show_levels
                status ="включен"if self .show_levels else "выключен"
            elif button ==7 :
                self .running =False
        self .button_states [button ]=pressed
    def control_loop (self ):
        clock =pygame .time .Clock ()
        while self .running :
            pygame .event .pump ()
            for i in range (self .joystick .get_numbuttons ()):
                button_pressed =self .joystick .get_button (i )
                if button_pressed or i in self .button_states :
                    self .handle_button_press (i ,button_pressed )
            clock .tick (60 )
    def run (self ):
        if not hasattr (self ,'joystick')or not self .vibration_supported :
            return
        if not hasattr (self ,'audio_stream')or self .audio_stream is None :
            return
        try :
            self .audio_stream .start ()
            self .control_loop ()
        except KeyboardInterrupt :
            pass
        except Exception as e :
            pass
        finally :
            self .cleanup ()
    def cleanup (self ):
        self .running =False
        if self .vibration_supported :
            self .joystick .rumble (0 ,0 ,0 )
        if hasattr (self ,'audio_stream')and self .audio_stream :
            try :
                self .audio_stream .stop ()
                self .audio_stream .close ()
            except :
                pass
        pygame .quit ()
def main ():
    try :
        controller =SimpleAudioVibrateController ()
        controller .run ()
    except ImportError as e :
        pass
    except Exception as e :
        pass
if __name__ =="__main__":
    main ()