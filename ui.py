import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class TimelineApp(tb.Window):
    def __init__(self):
        super().__init__(title="Timeline Drag & Drop Multi-pistes", size=(1000, 500))
        self.configure(padx=20, pady=20)

        ttk.Label(self, text="🎬 Éditeur Vidéo - Timeline", bootstyle="primary inverse", font=("Helvetica", 16)).pack(pady=10)

        # Canvas pour positionnement libre pendant le drag
        self.canvas = tk.Canvas(self, height=200, bg="#222222", highlightthickness=0)
        self.canvas.pack(fill="x", pady=10)

        # 2 pistes en tant que Frames
        self.tracks = []
        self.track_frames = []
        for i in range(2):
            frame = ttk.Frame(self.canvas, height=80, style="dark")
            window = self.canvas.create_window(0, i * 100, anchor="nw", window=frame, width=980)
            self.track_frames.append(frame)
            self.tracks.append(window)

        controls = ttk.Frame(self)
        controls.pack(pady=10)

        ttk.Label(controls, text="Ajouter un élément :", font=("Helvetica", 12)).pack(side="left", padx=5)
        for name in ["Image A", "Image B", "Clip C"]:
            btn = ttk.Button(controls, text=name, bootstyle="success", command=lambda n=name: self.add_block(n))
            btn.pack(side="left", padx=5)

        self.drag_data = {"widget": None, "x": 0, "y": 0, "from_track": None}

    def add_block(self, name):
        frame = self.track_frames[0]  # ajoute par défaut à la première piste
        block = ttk.Label(frame, text=name, bootstyle="info", padding=5)
        block.pack(side="left", padx=4, pady=4)

        block.bind("<Button-1>", self.on_drag_start)
        block.bind("<B1-Motion>", self.on_drag_motion)
        block.bind("<ButtonRelease-1>", self.on_drag_release)
        block.track_frame = frame

    def on_drag_start(self, event):
        widget = event.widget
        self.drag_data["widget"] = widget
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.drag_data["from_track"] = widget.track_frame

        # On crée un clone temporaire dans le canvas pour le déplacer librement
        widget.update_idletasks()
        self.canvas_drag = self.canvas.create_window(event.x_root - self.winfo_rootx(),
                                                     event.y_root - self.winfo_rooty(),
                                                     window=widget, anchor="nw")
        widget.pack_forget()

    def on_drag_motion(self, event):
        if not self.drag_data["widget"]:
            return
        dx = event.x_root - self.winfo_rootx()
        dy = event.y_root - self.winfo_rooty()
        self.canvas.coords(self.canvas_drag, dx, dy)

    def on_drag_release(self, event):
        widget = self.drag_data["widget"]
        if not widget:
            return

        self.canvas.delete(self.canvas_drag)

        # Trouver la piste cible
        drop_y = event.y_root - self.canvas.winfo_rooty()
        target_index = drop_y // 100

        if 0 <= target_index < len(self.track_frames):
            frame = self.track_frames[target_index]
        else:
            # Retour piste d’origine si drop invalide
            frame = self.drag_data["from_track"]

        widget.track_frame = frame
        widget.pack(in_=frame, side="left", padx=4, pady=4)

        self.drag_data = {"widget": None, "x": 0, "y": 0, "from_track": None}

if __name__ == "__main__":
    app = TimelineApp()
    app.mainloop()
