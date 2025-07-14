import hashlib
import os
import subprocess
import pygame

import requests

from element.sound import eSound

API_KEY = "sk_a4ea9842ff92c551a2190616767d8f558e3318d0c397324b"


# Caroline: kwhMCf63M8O3rCfnQ3oQ


class eVoice:
    def __init__(self, id = 'kwhMCf63M8O3rCfnQ3oQ', text = None):
        self.id = id
        self.text = text
        self.volume = 0.8

        text_bytes = text.encode('utf-8')
        self.hash = hashlib.md5(text_bytes).hexdigest()
        #TODO: path should be configurable
        output_path = "c:\\PYGAME\\media\\voices\\"
        self.path = f"{output_path}{self.id}_{self.hash}.mp3"

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if not os.path.isfile(self.path):
            self.download()

        self.eSound = eSound(path=self.path,volume=0.8, loop=False)
        
      
        
    def enabled(self):
        return self.text is not None
    
    
    def play(self, start):
        self.eSound.play(start)


    def download(self):
        
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.id}",  # ID d'une voix
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": API_KEY
            },
            json={
                "text": self.text,
                "voice_settings": {
                    "stability": 0.3,
                    "speed": 1.1,
                    "similarity_boost": 0.7
                }
            },verify=False
        )

        # Sauvegarde en MP3
        with open(self.filepath, "wb") as f:
            f.write(response.content)
            
    def schema(self):
        return {
            "id": ("str", "Voice Id"),
            "text": ("str", "Text"),
        }