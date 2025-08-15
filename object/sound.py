from tkinter import Image
from element.sound import eSound
from element.step import eStep
from object.object import Object
from PIL import Image, ImageDraw, ImageFont, ImageTk

class Sound(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)     
        self.sound     = eSound(**self.config("sound", {}))
        self.thumb = None

    def _draw(self, ctx):
        if( self.first_draw ):
            self.sound.play(self.age)

    def _schema(self):
        return {
            "sound": ("sound", "Sound")
        }
    
    def _prepare(self):
        pass

    @classmethod
    def parameter_fields(cls):
        return {
            "step": eStep.parameter_fields(),
            "sound": eSound.parameter_fields(),
        }
    
    
    def get_description(self):
        return self.sound.path

    def get_thumb(self):
        if self.thumb is None:
            # Génère une image vide avec fond transparent
            img = Image.new("RGBA", (17, 30), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Dessine une note de musique ou une forme
            try:
                # Essayons d’utiliser un emoji si le système supporte
                font = ImageFont.truetype("seguiemj.ttf", 14)  # police emoji sur Windows
                draw.text((0, 5), "🎵", font=font, fill=(30, 144, 255, 255))  # bleu doux
            except:
                # Sinon, forme simple
                draw.ellipse((16, 16, 48, 48), fill=(30, 144, 255, 255))
                draw.line((36, 16, 36, 5), fill=(30, 144, 255, 255), width=4)

            self.thumb = ImageTk.PhotoImage(img)
        return self.thumb