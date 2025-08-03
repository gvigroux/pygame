import os
import subprocess
import pygame

class eSound:
    def __init__(self, path = None, volume = 0.5, loop = False):
        self.path = path
        self.volume = volume
        self.loop = loop


        self.tmp_sound = None
        self.sound_channel = None
        self.sound_start = 0
        self.sound_length = 0

        if( path is not None ):
            self.sound    = pygame.mixer.Sound(path)
            self.sound.set_volume(volume)
            self.sound_length = self.sound.get_length()


    def __getstate__(self):
        state = self.__dict__.copy()
        if "sound" in state:
            del state["sound"]
        if "tmp_sound" in state:
            del state["tmp_sound"]
        if "sound_channel" in state:
            del state["sound_channel"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if( self.path is not None ):
            self.sound    = pygame.mixer.Sound(self.path)
            self.sound.set_volume(self.volume)
        self.tmp_sound = None
        self.sound_channel = None
        self.sound_start = 0

    def enabled(self):
        return self.path is not None

    def play(self, start):

        if( not self.enabled() ):
            return
        
        if( start > self.sound_length ):
            return
        
        # If already playing, stop it (mainly for UI)
        if( (self.sound_channel is not None) and (self.sound_channel.get_busy()) ):
            if( abs(self.sound_start - start) > 0.5 ):
                if( self.tmp_sound is not None ):
                    self.tmp_sound.stop()
                self.sound_channel.stop()
                self.sound.stop()
                self.sound_start = start
            else:
                self.sound_start = start
                return

        if( start > 0.1 ):
            self.tmp_sound = self.extract_segment_ffmpeg(start)
            self.tmp_sound.set_volume(self.volume)
            self.sound_channel = self.tmp_sound.play()
            self.sound_start = start
            return
        self.tmp_sound = None
        self.sound_start = start
        self.sound_channel = self.sound.play(loops=self.loop)

    def stop(self):
        if( not self.enabled() ):
            return
        self.sound.stop()

    def schema(self):
        return {
            "path": ("str", "Path"),
            "volume": ("float", "Volume"),
            "loop": ("bool", "Loop"),
        }
    
    
    def extract_segment_ffmpeg(self, start, output_file="temp.wav"):
        with open(os.devnull, 'wb') as devnull:
            subprocess.run([
                "ffmpeg",
                "-y",  # overwrite
                "-loglevel", "quiet", 
                "-ss", str(start),
                "-i", self.path,
                "-acodec", "pcm_s16le",
                output_file
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return pygame.mixer.Sound(output_file)


    @classmethod
    def parameter_fields(cls):
        return [
            {"name": "path", "type": "file"},
            {"name": "volume", "type": "float", "default": 0.5}
        ]