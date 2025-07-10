import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class Timeline(ttk.Frame):
    def __init__(self, master, num_tracks=3, length=60, height=300,  on_clip_click=None, **kwargs):
        super().__init__(master, **kwargs)
        self.num_tracks = num_tracks
        self.length = length  # durée en secondes
        self.track_height = 40
        self.tick_height = 20  # hauteur de l'échelle de temps
        self.on_clip_click = on_clip_click

        # Canvas + Scrollbars
        total_height = num_tracks * self.track_height + self.tick_height
        self.canvas = tk.Canvas(
            self,
            bg="white",
            height=height,
            scrollregion=(0, 0, length * 50, total_height)
        )
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._draw_tracks()
        self._draw_time_scale()

        self.clips = []
        self._selected_clip = None
        self._drag_data = {"x": 0, "item": None}

    def _draw_tracks(self):
        for i in range(self.num_tracks):
            y = i * self.track_height
            self.canvas.create_rectangle(
                0, y, self.length * 50, y + self.track_height,
                outline="gray"
            )

    def _draw_time_scale(self):
        y = self.num_tracks * self.track_height
        for second in range(self.length + 1):
            x = second * 50
            self.canvas.create_line(x, y, x, y + 10, fill="black", tags="time_scale")
            self.canvas.create_text(x + 2, y + 15, text=f"{second}s", anchor="nw", font=("Arial", 8), tags="time_scale")

        self.canvas.create_line(0, y, self.length * 50, y, fill="black", tags="time_scale")

    def add_track(self):
        """Ajoute dynamiquement une ligne/track à la timeline"""
        self.num_tracks += 1

        # 1️⃣ Dessine la nouvelle ligne à la bonne position
        y = (self.num_tracks - 1) * self.track_height
        self.canvas.create_rectangle(
            0, y, self.length * 50, y + self.track_height,
            outline="gray"
        )

        # 2️⃣ Efface et redessine l'échelle de temps pour qu'elle soit alignée en bas
        self.canvas.delete("time_scale")  # utilise un tag pour tout ce qui est time_scale
        self._draw_time_scale()

        # 3️⃣ Ajuste le scrollregion du canvas pour qu’il scroll jusqu’en bas du nouveau track
        total_height = self.num_tracks * self.track_height + self.tick_height
        self.canvas.config(scrollregion=(0, 0, self.length * 50, total_height))
        

    def add_track_top(self):
        """Ajoute dynamiquement une piste EN HAUT de la timeline"""
        self.num_tracks += 1

        # Décale tous les clips existants vers le bas
        for clip in self.clips:
            self.canvas.move(clip["rect_id"], 0, self.track_height)
            self.canvas.move(clip["text_id"], 0, self.track_height)

        # Décale l'échelle de temps vers le bas
        self.canvas.move("time_scale", 0, self.track_height)

        # Dessine le nouveau track EN HAUT
        y = 0
        self.canvas.create_rectangle(
            0, y, self.length * 50, y + self.track_height,
            outline="gray"
        )

        # Ajuste le scrollregion
        total_height = self.num_tracks * self.track_height + self.tick_height
        self.canvas.config(scrollregion=(0, 0, self.length * 50, total_height))
        return 0

        
    def add_clip(self, object, track, start, duration):
        x1 = start * 50        
        x2 = x1 + duration * 50
        if( duration < 0 ):
            x2 =  self.length * 50 - x1
        y1 = track * self.track_height + 5
        y2 = y1 + self.track_height - 10

        # Crée le rectangle
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="skyblue", outline="black"
        )

        # Texte aligné à gauche
        text_margin = 5  # marge interne
        text_id = self.canvas.create_text(
            x1 + text_margin,
            (y1 + y2) / 2,
            text=object.label,
            fill="black",
            font=("Arial", 10),
            anchor="w"  # ancre à gauche
        )

        # Stocke le couple (rect, text)
        self.clips.append({
            "rect_id": rect_id,
            "text_id": text_id,
            "object": object
        })

        # Bind drag pour le rectangle ET le texte
        for item_id in (rect_id, text_id):
            self.canvas.tag_bind(item_id, "<ButtonPress-1>", self._on_start_drag)
            self.canvas.tag_bind(item_id, "<B1-Motion>", self._on_drag)
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self._on_clip_click)


    def _on_clip_click(self, event):
        dx = abs(event.x - self._drag_data["start_x"])
        seuil = 5
        if dx > seuil:
            return

        item = self.canvas.find_closest(event.x, event.y)[0]

        for clip in self.clips:
            if item in (clip["rect_id"], clip["text_id"]):
                # 1️⃣ Désélectionne l'ancien clip
                if self._selected_clip:
                    self.canvas.itemconfig(self._selected_clip["rect_id"], fill="skyblue")

                # 2️⃣ Sélectionne le nouveau
                self.canvas.itemconfig(clip["rect_id"], fill="orange")
                self._selected_clip = clip

                # 3️⃣ Callback vers le monde extérieur
                if self.on_clip_click:
                    self.on_clip_click(clip["object"])

                break



    def _on_start_drag(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        self._drag_data["item"] = item
        self._drag_data["x"] = event.x
        self._drag_data["start_x"] = event.x


    def _on_drag(self, event):
        pixels_per_second = 50
        step_s = 0.1
        step_px = step_s * pixels_per_second

        raw_dx = event.x - self._drag_data["x"]
        steps = int(raw_dx / step_px)

        if steps != 0:
            real_dx = steps * step_px

            #for rect_id, text_id in self.clips:
            #    if self._drag_data["item"] in (rect_id, text_id):
                    
            for clip in self.clips:
                if self._drag_data["item"] in (clip["rect_id"], clip["text_id"]):
                    # Vérifie les limites
                    coords = self.canvas.coords(clip["rect_id"])
                    x1, y1, x2, y2 = coords

                    new_x1 = x1 + real_dx
                    new_x2 = x2 + real_dx

                    timeline_left = 0
                    timeline_right = self.length * pixels_per_second

                    # Si ça dépasse à gauche → ajuste le déplacement
                    if new_x1 < timeline_left:
                        real_dx = timeline_left - x1  # ramène à zéro

                    # Si ça dépasse à droite → ajuste le déplacement
                    if new_x2 > timeline_right:
                        real_dx = timeline_right - x2  # ramène à la limite

                    # Applique le déplacement corrigé
                    self.canvas.move(clip["rect_id"], real_dx, 0)
                    self.canvas.move(clip["text_id"], real_dx, 0)

                    # Apply new value to object
                    clip["object"].step.delay = round(clip["object"].step.delay + real_dx / pixels_per_second, 1)
                    clip["object"].data["step"]["delay"] = clip["object"].step.delay                    
                    break

            self._drag_data["x"] += real_dx


