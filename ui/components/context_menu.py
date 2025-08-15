import tkinter as tk

class FlatContextMenu(tk.Toplevel):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.overrideredirect(True)

        colors = parent.state["colors"]
        fg          ="white"
        bg          = colors.get("unselected_bg")
        hover_bg    = colors.get("hovered_bg")

        # Couleur de la bordure : couleur du Toplevel
        self.configure(bg=hover_bg)

        # Frame intérieure avec fond du menu
        self.inner_frame = tk.Frame(self, bg=bg)
        self.inner_frame.pack(padx=1, pady=1)

        self.buttons = []
        for label, cmd in items:
            btn = tk.Label(self.inner_frame, text=label, bg=bg, fg=fg,
                           anchor="w", padx=10, pady=4)
            btn.default_bg = bg
            btn.pack(fill="x")
            self.buttons.append(btn)

            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=hover_bg))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b.default_bg))
            btn.bind("<Button-1>", lambda e, c=cmd: (c() if callable(c) else None, self.destroy()))

        self.bind("<FocusOut>", lambda e: self.destroy())

    def popup(self, x, y):
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.update_idletasks()  # force l'application du style
        for btn in self.buttons:
            btn.configure(bg=btn.default_bg)  # réapplique la bonne couleur
        self.focus_force()
