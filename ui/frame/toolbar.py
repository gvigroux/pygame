import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *



from ui.frame.tooltip import Tooltip
from ui.helper import colorize_icon


class Toolbar:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, style="secondary.TFrame")
        self.frame.grid(row=0, column=0, sticky="ew")
        self.icons = []  

    def add_icon(self, icon_path, command, tooltip=None, color=(185, 185, 185), hover_color=(255, 255, 255)):
        icon_normal = colorize_icon(icon_path, color)
        icon_hover  = colorize_icon(icon_path, hover_color)

        btn = ttk.Button(self.frame, image=icon_normal, command=command, style="Tool.TButton", cursor="hand2")
        btn.image_normal    = icon_normal
        btn.image_hover     = icon_hover

        btn.bind("<Enter>", lambda e: btn.config(image=btn.image_hover))
        btn.bind("<Leave>", lambda e: btn.config(image=btn.image_normal))

        btn.pack(side="left", padx=2, pady=2)
        self.icons.append(icon_normal)
        self.icons.append(icon_hover)
        if tooltip:
            Tooltip(btn, tooltip)

    def add_separator(self, width=1, color="#555"):
        sep = ttk.Frame(self.frame, width=width)
        sep.pack(side="left", fill="y", padx=5, pady=5)

    def add_text(self, text, padding=(10, 5)):
        label = ttk.Label(
            self.frame,
            text=text,
            style="Tool.TButton",
            foreground="#B9B9B9",  # couleur du texte
        )
        label.pack(side="left", padx=padding[0], pady=padding[1])

