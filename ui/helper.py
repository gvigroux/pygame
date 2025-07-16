
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from PIL import Image, ImageTk, ImageOps

def lighten_color(hex_color, factor=0.1):
    """Éclaircit une couleur hex de `factor` (0.1 = +10%)"""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = min(int(r + (255 - r) * factor), 255)
    g = min(int(g + (255 - g) * factor), 255)
    b = min(int(b + (255 - b) * factor), 255)

    return f"#{r:02x}{g:02x}{b:02x}"

def get_calculated_value(obj, key):
    method = "get_" + key
    if hasattr(obj, method) and callable(getattr(obj, method, "")):
        return eval("obj."+method + "()")
    return getattr(obj, key, "")
 

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




def center_window(window, window_width, window_height):
        
    # Obtenir la taille de l'écran
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculer les coordonnées
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Appliquer la géométrie centrée
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")


# def center_window(window, parent=None):
#     window.update_idletasks()  # Force le calcul de la taille

#     width = window.winfo_width()
#     height = window.winfo_height()

#     if parent is None:
#         parent = window.master

#     x = parent.winfo_x()
#     y = parent.winfo_y()
#     parent_width = parent.winfo_width()
#     parent_height = parent.winfo_height()

#     new_x = x + (parent_width - width) // 2
#     new_y = y + (parent_height - height) // 2

#     window.geometry(f"{width}x{height}+{new_x}+{new_y}")


   

def center_on_parent(window):
    """
    Centre une Toplevel sur son parent.
    """
    window.update_idletasks()

    parent = window.master

    w = window.winfo_width()
    h = window.winfo_height()

    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()

    x = px + (pw - w) // 2
    y = py + (ph - h) // 2

    window.geometry(f"{w}x{h}+{x}+{y}")

def place_under_mouse(window):
    """
    Place une Toplevel sous le curseur.
    """
    window.update_idletasks()

    w = window.winfo_width()
    h = window.winfo_height()

    x = window.winfo_pointerx()
    y = window.winfo_pointery()

    window.geometry(f"{w}x{h}+{x}+{y}")
