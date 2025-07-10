
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


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
