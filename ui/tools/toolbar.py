import ttkbootstrap as ttk
from ttkbootstrap.constants import *


from PIL import Image, ImageTk, ImageOps


class Toolbar:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="ew")
        #self.frame.pack(side="top", fill="x")
        self.icons = []  

    def add_icon(self, icon_path, command, color=(255, 255, 255)):
        icon = colorize_icon(icon_path, color)
        btn = ttk.Button(self.frame, image=icon, command=command)
        btn.pack(side="left", padx=2, pady=2)
        self.icons.append(icon) 



def colorize_icon(path, new_color=(255, 0, 0)):
    """
    Ouvre un PNG noir et transparent et remplace le noir par new_color.
    """
    img = Image.open(path).convert("RGBA")

    # Séparer alpha
    r, g, b, a = img.split()

    # Convertir l’image en noir & blanc (mask)
    gray = ImageOps.grayscale(img)
    # Inverser : noir devient blanc
    mask = ImageOps.invert(gray)

    # Créer une image couleur unie
    color_img = Image.new("RGBA", img.size, new_color + (0,))

    # Coller la couleur uniquement où c’était noir
    colored = Image.composite(color_img, Image.new("RGBA", img.size), mask)
    colored.putalpha(a)

    return ImageTk.PhotoImage(colored)
