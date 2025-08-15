import tkinter as tk
import ttkbootstrap as ttk


  
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # 🟡 Création du Canvas et Scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 🟡 Frame interne dans le Canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # 🟡 Placement en grille
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # 🧠 Resize automatique du contenu
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 🖱️ Support de la molette
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

    def _on_canvas_configure(self, event):
        # 🛠️ Calculer la largeur disponible (canvas - scrollbar)
        canvas_width = self.canvas.winfo_width()
        scrollbar_width = self.scrollbar.winfo_width()
        
        usable_width = canvas_width - scrollbar_width
        if usable_width <= 0:
            return  # ignore les valeurs absurdes

        # ✅ Ne pas redimensionner inutilement (évite clignotement)
        if hasattr(self, "_last_width") and self._last_width == usable_width:
            return

        self._last_width = usable_width
        self.canvas.itemconfig(self.window_id, width=usable_width)


    def _on_frame_configure(self, event):
        """Mets à jour la scrollregion du canvas après changement du contenu."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        direction = -1 if event.num == 4 or event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def get_content_frame(self):
        return self.scrollable_frame
