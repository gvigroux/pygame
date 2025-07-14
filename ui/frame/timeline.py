import copy
import math
import os
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import tkinter.font as tkfont

from background.video import Video
from ui.helper import colorize_icon


def color_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_color(rgb):
    return "#%02x%02x%02x" % rgb

def darken(hex_color, factor=0.8):
    """Assombrit une couleur hex"""
    rgb = color_to_rgb(hex_color)
    dark_rgb = tuple(int(c * factor) for c in rgb)
    return rgb_to_color(dark_rgb)


class Timeline(ttk.Frame):
    def __init__(self, master, num_tracks=3, length=60, height=300, on_clip_click=None, on_clip_add=None, on_clip_removed=None, on_time_click = None, on_video_update = None ,**kwargs):
        self.on_clip_click = on_clip_click
        self.num_tracks = num_tracks
        self.length = length
        self.track_height = 40
        self.tick_height = 20
        self.on_clip_removed = on_clip_removed
        self.has_background = True  # ajoute une piste "background"
        self.on_time_click = on_time_click
        self.on_video_update = on_video_update
        self.on_clip_add = on_clip_add

        super().__init__(master, **kwargs)

        style = ttk.Style("superhero")
        colors = style.colors    # Dictionnaire des couleurs
        self.style_clip_bg = colors.get("secondary")
        self.style_clip_fg = "white"
        self.style_clip_bd = darken(self.style_clip_bg)
        self.style_clip_selected_bg = self.style_clip_bg
        self.style_clip_selected_fg = self.style_clip_fg
        self.style_clip_selected_bd = colors.get("primary")


        # === Zone des headers ===
        self.headers_frame = ttk.Frame(self)
        self.headers_frame.grid(row=0, column=0, sticky="ns")
        self.headers_frame.columnconfigure(0, weight=1)

        # === Canvas + Scrollbars ===
        total_height = num_tracks * self.track_height + self.tick_height
        self.canvas = tk.Canvas(
            self,
            bg="white",
            height=height,
            scrollregion=(0, 0, length * 50, total_height)
        )
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=2, sticky="ns")
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.canvas.configure(xscrollcommand=self.h_scroll.set)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Playhead management
        self.playhead_line_id = None
        self.current_time = 0.0
        self.is_playing = False
        self.canvas.focus_set()
        self.canvas.bind("<Left>", self.move_playhead_left)
        self.canvas.bind("<Right>", self.move_playhead_right)
        self.canvas.bind("<space>", self.toggle_playback)

        self.clips = []
        self.icons = []
        self._draw_headers()
        self._draw_tracks()
        self._draw_time_scale()
        self.canvas._accepts_drop = True  # important !

        self._selected_clip = None
        self._drag_data = {"x": 0, "item": None, "start_x": 0}
        self._resize_data = {"clip": None, "side": None, "start_x": 0}
        
        self.canvas.bind("<Delete>", self.delete_selected_clip) 
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def reset(self):

        clips_to_remove = [clip for clip in self.clips ]
        for clip in clips_to_remove:
            for key in ("rect_id", "text_id", "left_handle", "right_handle", "thumb_id"):
                self.canvas.delete(clip[key])
            self.clips.remove(clip)      
            if self.on_clip_removed:      
                self.on_clip_removed(clip["object"])

        for index in range(self.num_tracks):
            self._remove_track(index)
        
        self.icons = []
        self._selected_clip = None
        self._draw_headers()
        self._draw_tracks()
        self._draw_time_scale()

    def move_playhead_left(self, event=None):
        self.current_time = max(0.0, self.current_time - 0.1)
        self.update_playhead_and_preview()

    def move_playhead_right(self, event=None):
        self.current_time = min(self.length, self.current_time + 0.1)
        self.update_playhead_and_preview()

    def update_playhead_and_preview(self):
        x = self.current_time * 50  # 50 pixels par seconde

        total_height = (self.num_tracks + int(self.has_background)) * self.track_height + self.tick_height*2
        if self.playhead_line_id:
            self.canvas.coords(self.playhead_line_id, x, 0, x, total_height)
        else:
            # Calcul de la hauteur de la ligne
            self.playhead_line_id = self.canvas.create_line(x, 0, x, total_height, fill="red", width=2, dash=(4, 2))            

        if self.on_time_click:
            self.on_time_click(self.current_time)

    def toggle_playback(self, event=None):
        if self.is_playing:
            self.is_playing = False
        else:
            self.is_playing = True
            self.play_loop()

    def play_loop(self):
        if not self.is_playing:
            return
        
        start_time = time.perf_counter()  # ⏱ début précis
    
        self.current_time += 0.05
        if self.current_time >= self.length:
            self.current_time = self.length
            self.is_playing = False
            return

        self.update_playhead_and_preview()
        
        # 🧮 durée écoulée
        elapsed = (time.perf_counter() - start_time) * 1000  # en ms
        delay = max(0, int(50 - elapsed))  # évite d'appeler avec délai négatif

        #print(f"Elapsed: {elapsed:.2f} ms")
        # Refaire appel à cette fonction après 50ms
        self.after(delay, self.play_loop)


    def truncate_text(self, text, max_width, font):
        """Retourne un texte tronqué avec '...' si trop large."""
        if font.measure(text) <= max_width:
            return text
        else:
            # On tronque progressivement jusqu'à ce que ça rentre
            for i in range(len(text), 0, -1):
                truncated = text[:i] + "..."
                if font.measure(truncated) <= max_width:
                    return truncated
            return "..."  # au pire
        

    def _on_canvas_click(self, event):
        self.canvas.focus_set() 

        if not self.on_time_click:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Calcul de la position verticale de la bande de l'échelle de temps
        total_tracks = self.num_tracks + int(self.has_background)
        time_scale_y = total_tracks * self.track_height

        # Seulement si on clique dans la bande de l'échelle de temps
        if time_scale_y <= y <= time_scale_y + self.tick_height*2:
            time_in_seconds = round(x / 50, 2)
            self.current_time = time_in_seconds
            self.update_playhead_and_preview()
            #self.on_time_click(time_in_seconds)

            # Supprimer l'ancienne ligne si elle existe
            #if self.playhead_line_id:
            #    self.canvas.delete(self.playhead_line_id)

            #x_pos = x  # position cliquée

            # Calcul de la hauteur de la ligne
            #total_height = (self.num_tracks + int(self.has_background)) * self.track_height + self.tick_height

            # Dessine une nouvelle ligne verticale rouge
            #self.playhead_line_id = self.canvas.create_line(
            #    x_pos, 0, x_pos, total_height,
            #    fill="red", width=2, dash=(4, 2), tags="playhead"
            #)


    def _draw_headers(self):
        for i in range(self.num_tracks):
            frame = ttk.Frame(self.headers_frame)
            frame.grid(row=i, column=0, sticky="nsew")
            self.headers_frame.grid_rowconfigure(i, minsize=self.track_height)

            lbl = ttk.Label(
                frame,
                text=f"Track {i+1}",
                anchor="center",
                padding=5
            )
            lbl.pack(side="left", fill="x", expand=True)

            #btn = ttk.Button(frame, text="X", width=2,
            #                command=lambda track=i: self._remove_track(track))
            icon_path = "ui/icons/icons8-annuler-12.png"
            icon_normal = colorize_icon(icon_path, (185, 185, 185))
            icon_hover  = colorize_icon(icon_path, (255, 255, 255))
            btn = ttk.Button(frame, image=icon_normal, command=lambda track=i: self._remove_track(track), style="Tool.TButton", cursor="hand2") 
            btn.image_normal    = icon_normal
            btn.image_hover     = icon_hover

            btn.bind("<Enter>", lambda e, b=btn: b.config(image=b.image_hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(image=b.image_normal))
            btn.pack(side="right", padx=2, pady=2)
            self.icons.append(icon_normal)
            self.icons.append(icon_hover)

        if self.has_background:
            i = self.num_tracks
            lbl = ttk.Label(
                self.headers_frame,
                text="Background",
                anchor="center",
                padding=5,
                style="secondary.TLabel"
            )
            lbl.grid(row=i, column=0, sticky="nsew")
            self.headers_frame.grid_rowconfigure(i, minsize=self.track_height)

        self.headers_frame.grid_rowconfigure(self.num_tracks + int(self.has_background), minsize=self.tick_height)
        self.headers_frame.configure(width=100)

    def _draw_tracks(self):        
        # 🧹 Nettoyer les anciennes pistes
        self.canvas.delete("track_rect")

        total_tracks = self.num_tracks + int(self.has_background)
        total_height = total_tracks * self.track_height + self.tick_height
        self.canvas.config(scrollregion=(0, 0, self.length * 50, total_height))
        for i in range(total_tracks):
            y = i * self.track_height
            self.canvas.create_rectangle(
                0, y, self.length * 50, y + self.track_height,
                outline="gray",
                tags="track_rect" 
            )

    def _draw_time_scale(self):
        total_tracks = self.num_tracks + int(self.has_background)
        y = total_tracks * self.track_height
        for second in range(self.length + 1):
            x = second * 50
            self.canvas.create_line(x, y, x, y + 10, fill="black", tags="time_scale")
            self.canvas.create_text(x + 2, y + 15, text=f"{second}s", anchor="nw", font=("Arial", 8), tags="time_scale")
        self.canvas.create_line(0, y, self.length * 50, y, fill="black", tags="time_scale")

        #self.canvas.tag_bind("time_scale", "<Button-1>", self._on_time_scale_click)

    #def _on_time_scale_click(self, event):
    #    x = self.canvas.canvasx(event.x)
    #    seconds = round(x / 50, 2)  # ou int(x / 50) pour une valeur entière
    #    if self._on_time_click_callback:
    #        self._on_time_click_callback(seconds)

    def _remove_track(self, track_index):
        # Supprimer tous les clips de cette piste
        clips_to_remove = [clip for clip in self.clips if clip["track"] == track_index]
        for clip in clips_to_remove:
            for key in ("rect_id", "text_id", "left_handle", "right_handle"):
                self.canvas.delete(clip[key])
            self.clips.remove(clip)      
            if self.on_clip_removed:      
                self.on_clip_removed(clip["object"])
            
        # Décaler toutes les pistes et clips en dessous vers le haut
        for clip in self.clips:
            if( isinstance(clip["track"], str) ):
                continue
            if( isinstance(track_index, str) ):
                continue
            if clip["track"] > track_index:
                clip["track"] -= 1
                self.canvas.move(clip["rect_id"], 0, -self.track_height)
                self.canvas.move(clip["text_id"], 0, -self.track_height)
                self.canvas.move(clip["left_handle"], 0, -self.track_height)
                self.canvas.move(clip["right_handle"], 0, -self.track_height)

        if self.has_background:
            for clip in self.clips:
                if clip["track"] == "background":
                    self.canvas.move(clip["rect_id"], 0, -self.track_height)
                    self.canvas.move(clip["text_id"], 0, -self.track_height)
                    self.canvas.move(clip["left_handle"], 0, -self.track_height)
                    self.canvas.move(clip["right_handle"], 0, -self.track_height)
                    if clip.get("thumb_id"):
                        self.canvas.move(clip["thumb_id"], 0, -self.track_height)

        self.canvas.move("time_scale", 0, -self.track_height)
        self.num_tracks -= 1

        # Re-dessiner headers et pistes
        for widget in self.headers_frame.winfo_children():
            widget.destroy()
        self._draw_headers()

        self._draw_tracks()

        # Ajuster la hauteur scrollregion
        total_tracks = self.num_tracks + int(self.has_background)
        total_height = total_tracks * self.track_height + self.tick_height
        self.canvas.config(scrollregion=(0, 0, self.length * 50, total_height))


    def add_track_top(self, move_clips=True):
        """Ajoute dynamiquement une piste EN HAUT de la timeline"""
        self.num_tracks += 1

        # Décale tous les clips existants vers le bas
        if( move_clips ):
            for clip in self.clips:
                self.canvas.move(clip["rect_id"], 0, self.track_height)
                self.canvas.move(clip["text_id"], 0, self.track_height)
                self.canvas.move(clip["left_handle"], 0, self.track_height)
                self.canvas.move(clip["right_handle"], 0, self.track_height)

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

        for widget in self.headers_frame.winfo_children():
            widget.destroy()
        self._draw_headers()

    
    
    def _on_resize_start(self, event, side):
        if self._drag_data["item"]:
            return  # ignore si drag en cours
        x = self.canvas.canvasx(event.x)  # CORRECTION
        y = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)[0]
        for clip in self.clips:
            if item in (clip["left_handle"], clip["right_handle"]):
                self._resize_data = {"clip": clip, "side": side, "start_x": x}
                break


    def _on_resize(self, event, side):
        clip = self._resize_data.get("clip")
        if not clip:
            return

        x = self.canvas.canvasx(event.x)  # CORRECTION
        x1, y1, x2, y2 = self.canvas.coords(clip["rect_id"])

        if side == "left":
            new_x1 = min(max(x, 0), x2 - 10)  # min 10px
            new_x2 = x2
        else:
            new_x1 = x1
            new_x2 = max(x, x1 + 10)

        self.canvas.coords(clip["rect_id"], new_x1, y1, new_x2, y2)

        handle_size = 5
        self.canvas.coords(clip["left_handle"], new_x1 - handle_size, y1, new_x1 + handle_size, y2)
        self.canvas.coords(clip["right_handle"], new_x2 - handle_size, y1, new_x2 + handle_size, y2)

        # ✅ Bouge le texte si resize gauche
        
        text_x, text_y = self.canvas.coords(clip["text_id"])
        new_text_x = new_x1 + 5
        if side == "left":
            self.canvas.coords(clip["text_id"], new_text_x, text_y)
            
        # Calcule largeur dispo pour le texte
        max_text_width = new_x2 - new_text_x - 5  # 5px marge à droite

        # Récupère le texte original complet (par exemple dans clip["object"].label)
        original_text = clip["object"].label

        font = tkfont.Font(family="Arial", size=10)
        truncated_text = self.truncate_text(original_text, max_text_width, font)

        self.canvas.coords(clip["text_id"], new_text_x, text_y)
        self.canvas.itemconfig(clip["text_id"], text=truncated_text, font=font)

        pixels_per_second = 50
        duration = (new_x2 - new_x1) / pixels_per_second
        clip["object"].step.duration = round(duration, 1)
        clip["object"].data.setdefault("step", {})["duration"] = clip["object"].step.duration


    def _on_resize_end(self, event):
        clip = self._resize_data.get("clip")
        if clip and clip["track"] != "background":
            self._resolve_overlaps_on_track(clip["track"])
        elif clip and clip["track"] == "background":
            self._reorder_background_clips()
        self._resize_data = {"clip": None, "side": None, "start_x": 0}

    def add_clip(self, object, track, start, duration):
        if track == "background":
            track_index = "background" #self.num_tracks  # dernière ligne
        else:
            track_index = track
    
        
        x1 = start * 50
        x2 = x1 + duration * 50
        if( duration < 0 ):
            x2 =  self.length * 50 - x1
        if track == "background":
            y1 = self.num_tracks * self.track_height + 5
        else:
            y1 = track_index * self.track_height + 5
        y2 = y1 + self.track_height - 10
        
        thumb_id = None
        if track == "background":
            rect_id     = self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.style_clip_bg, outline=self.style_clip_bd)
            thumb_id    = self.canvas.create_image(x1, y1, anchor="nw", image=object.get_thumb())
        else:
            rect_id     = self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.style_clip_bg, outline=self.style_clip_bd)
         
        font = tkfont.Font(family="Arial", size=10)
        max_text_width = (x2 - x1) - 10  # 10 pixels de marge à droite
        
        display_text = self.truncate_text(object.label, max_text_width, font)

        text_id = self.canvas.create_text(x1 + 5, (y1 + y2) / 2, text=display_text, anchor="w", font=font, fill=self.style_clip_fg)

        
        handle_size = 5
        left_handle = self.canvas.create_rectangle(x1 - handle_size, y1, x1 + handle_size, y2, fill="", outline="")
        right_handle = self.canvas.create_rectangle(x2 - handle_size, y1, x2 + handle_size, y2, fill="", outline="")

        self.clips.append({
            "rect_id": rect_id,
            "text_id": text_id,
            "left_handle": left_handle,
            "right_handle": right_handle,
            "object": object,
            "track": track_index,
            "thumb_id": thumb_id
        })

        for item_id in (rect_id, text_id):
            self.canvas.tag_bind(item_id, "<ButtonPress-1>", self._on_clip_press)
            self.canvas.tag_bind(item_id, "<B1-Motion>", self._on_drag)
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self._on_clip_release)
            self.canvas.tag_bind(item_id, "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
            self.canvas.tag_bind(item_id, "<Leave>", lambda e: self.canvas.config(cursor=""))

        for handle_id, side in ((left_handle, "left"), (right_handle, "right")):
            self.canvas.tag_bind(handle_id, "<ButtonPress-1>", lambda e, s=side: self._on_resize_start(e, s))
            self.canvas.tag_bind(handle_id, "<B1-Motion>", lambda e, s=side: self._on_resize(e, s))
            self.canvas.tag_bind(handle_id, "<ButtonRelease-1>", self._on_resize_end)
            self.canvas.tag_bind(handle_id, "<Enter>", lambda e: self.canvas.config(cursor="sb_h_double_arrow"))
            self.canvas.tag_bind(handle_id, "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _on_clip_press(self, event):
        x = self.canvas.canvasx(event.x) 
        item = self.canvas.find_closest(x, event.y)[0]
        self._drag_data["item"] = item
        self._drag_data["x"] = x
        self._drag_data["start_x"] = x

    def _on_clip_release(self, event):
        x = self.canvas.canvasx(event.x)
        dx = abs(x - self._drag_data["start_x"])
        seuil = 5 # Seuil pour distinguer un clic d’un drag

        item = self._drag_data["item"]
        for clip in self.clips:
            if item in (clip["rect_id"], clip["text_id"]):
                if dx < seuil:
                    # clic
                    if self._selected_clip:
                        self.canvas.itemconfig(self._selected_clip["rect_id"], fill=self.style_clip_bg, outline=self.style_clip_bd)
                    self.canvas.itemconfig(clip["rect_id"], fill=self.style_clip_selected_bg, outline=self.style_clip_selected_bd)
                    self._selected_clip = clip
                    self.canvas.focus_set()
                    if self.on_clip_click:
                        self.on_clip_click(clip["object"])
                else:
                    # DRAG terminé → réaligner si besoin
                    if clip["track"] != "background":
                        self._resolve_overlaps_on_track(clip["track"])
                    else:
                        self._reorder_background_clips()
                break

        self._drag_data = {"x": 0, "item": None, "start_x": 0}


    def _on_start_drag(self, event):
        if self._resize_data["clip"]:
            return  # ignore drag si resize actif
        x = self.canvas.canvasx(event.x)  # CORRECTION
        item = self.canvas.find_closest(x, event.y)[0]
        self._drag_data = {"item": item, "x": x, "start_x": event.x}
  
   
    def _on_drag(self, event):
        if not self._drag_data["item"]:
            return

        item = self._drag_data["item"]
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        dx = x - self._drag_data["x"]
        self._drag_data["x"] = x

        for clip in self.clips:
            if item in (clip["rect_id"], clip["text_id"]):
                old_track = clip["track"]

                # === Mouvement horizontal
                self.canvas.move(clip["rect_id"], dx, 0)
                self.canvas.move(clip["text_id"], dx, 0)
                self.canvas.move(clip["left_handle"], dx, 0)
                self.canvas.move(clip["right_handle"], dx, 0)
                if clip.get("thumb_id"):
                    self.canvas.move(clip["thumb_id"], dx, 0)

                # === Met à jour le delay
                x1, _, _, _ = self.canvas.coords(clip["rect_id"])
                clip["object"].step.delay = round(x1 / 50.0, 2)

                # === Détection de track actuelle
                new_track = int(y // self.track_height)
                if 0 <= new_track < self.num_tracks and new_track != old_track:
                    # Décalage vertical
                    dy = (new_track - old_track) * self.track_height
                    self.canvas.move(clip["rect_id"], 0, dy)
                    self.canvas.move(clip["text_id"], 0, dy)
                    self.canvas.move(clip["left_handle"], 0, dy)
                    self.canvas.move(clip["right_handle"], 0, dy)
                    if clip.get("thumb_id"):
                        self.canvas.move(clip["thumb_id"], 0, dy)

                    clip["track"] = new_track
                break



    def _reorder_background_clips(self):
        """Réorganise les clips de la piste 'background' sans chevauchement et met à jour leur step.delay"""
      
        # 1. Récupérer et trier les clips de la piste 'background' par leur position logique (step.delay)
        background_clips = [
            clip for clip in self.clips if clip["track"] == "background"
        ]
        background_clips.sort(key=lambda clip: clip["object"].step.delay)

        # 2. Réaligner horizontalement tous les clips sans espace
        current_time = 0
        for clip in background_clips:
            obj = clip["object"]
            duration = obj.step.duration

            # Met à jour le start logique
            obj.step.delay = current_time  # utile si delay est utilisé aussi
            obj.data.setdefault("step", {})["start"] = current_time

            # Convertit en pixels
            x1 = current_time * 50
            x2 = x1 + duration * 50
            y1 = self.num_tracks * self.track_height + 5
            y2 = y1 + self.track_height - 10

            # Met à jour les éléments Canvas
            self.canvas.coords(clip["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(clip["left_handle"], x1 - 5, y1, x1 + 5, y2)
            self.canvas.coords(clip["right_handle"], x2 - 5, y1, x2 + 5, y2)
            self.canvas.coords(clip["text_id"], x1 + 5, (y1 + y2) / 2)

            if clip.get("thumb_id"):
                self.canvas.coords(clip["thumb_id"], x1, y1)

            current_time += duration


    def _on_clip_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        for clip in self.clips:
            if item in (clip["rect_id"], clip["text_id"]):
                if self._selected_clip:
                    self.canvas.itemconfig(self._selected_clip["rect_id"], fill="skyblue")
                self.canvas.itemconfig(clip["rect_id"], fill="orange")
                self._selected_clip = clip
                if self.on_clip_click:
                    self.on_clip_click(clip["object"])
                break


    def redraw(self):
        """Redessine tous les clips selon les valeurs de step.delay et step.duration"""
        for clip in self.clips:
            obj = clip["object"]
            start = obj.step.delay
            duration = obj.step.duration
            x1 = start * 50

            x2 = x1 + duration * 50
            if( duration < 0 ):
                x2 =  self.length * 50 - x1

            if clip["track"] == "background":
                y1 = self.num_tracks * self.track_height + 5
            else:
                y1 = clip["track"] * self.track_height + 5
            y2 = y1 + self.track_height - 10

            # Redessine les formes
            self.canvas.coords(clip["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(clip["left_handle"], x1 - 5, y1, x1 + 5, y2)
            self.canvas.coords(clip["right_handle"], x2 - 5, y1, x2 + 5, y2)

            # Repositionne l'image si elle existe
            if clip["thumb_id"]:
                self.canvas.coords(clip["thumb_id"], x1, y1)

            # Ajuste le texte
            font = tkfont.Font(family="Arial", size=10)
            max_text_width = (x2 - x1) - 10
            label = self.truncate_text(obj.label, max_text_width, font)
            self.canvas.coords(clip["text_id"], x1 + 5, (y1 + y2) / 2)
            self.canvas.itemconfig(clip["text_id"], text=label, font=font)



    def add_background_video(self, video, at_position) :
        video_copy = video.clone()
        canvas_x = self.canvas.canvasx(at_position[0])
        video_copy.step.delay = max((canvas_x / 50.0)-10, 0)
        self.add_clip(video_copy, track="background", start=video_copy.step.delay, duration= video_copy.step.duration)
        self._reorder_background_clips()
        self.redraw()

    def get_track_at_y(self, y):
        # Trouve la position du canvas dans la fenêtre globale
        canvas_y_on_screen = self.canvas.winfo_rooty()
        
        # Calcule le y relatif dans le canvas
        local_y = y - canvas_y_on_screen
        
        # Prend en compte le scroll
        canvas_y = self.canvas.canvasy(local_y)
        track_index = int(canvas_y // self.track_height)
        return track_index
    
    def drop_clip(self, object, at_position):
        # Conversion coordonnées écran → canevas
        screen_x, screen_y = at_position
        canvas_x = self.canvas.canvasx(screen_x - self.canvas.winfo_rootx())
        canvas_y = self.canvas.canvasy(screen_y - self.canvas.winfo_rooty())
        
        track_index = self.get_track_at_y(at_position[1])
        if track_index < 0 or track_index >= self.num_tracks:
            print(f"[DROP] Invalid track index: {track_index}")
            return

        # Crée un nouvel objet clip (selon ton système)
        object_copy = object.clone()
        object_copy.step.delay = max((canvas_x / 50.0), 0)
        print(f"[DROP] Adding clip at: {object_copy.step.delay:.2f} (track {track_index}) {canvas_x:.2f}")

        self.add_clip(object_copy, track=track_index, start=object_copy.step.delay, duration= object_copy.step.duration)
        self.on_clip_add(object_copy)
        self._resolve_overlaps_on_track(track_index)


    def _resolve_overlaps_on_track(self, track_index):
        """Décale les clips qui se chevauchent sur une track, récursivement"""

        # 1. Récupère les clips de la track concernée
        clips = [
            clip for clip in self.clips
            if clip["track"] == track_index and clip["object"].step.duration > 0
        ]

        # 2. Trie les clips par start time
        clips.sort(key=lambda c: c["object"].step.delay)

        for i in range(len(clips) - 1):
            current = clips[i]
            next_clip = clips[i + 1]

            current_start = current["object"].step.delay
            current_end = current_start + current["object"].step.duration

            next_start = next_clip["object"].step.delay
            next_duration = next_clip["object"].step.duration

            # Si overlap : on pousse le next_clip juste après current
            if next_start < current_end:
                new_start = current_end
                next_clip["object"].step.delay = new_start
                next_clip["object"].data.setdefault("step", {})["start"] = new_start

                # met à jour position canvas
                x1 = new_start * 50
                x2 = x1 + next_duration * 50
                y1 = track_index * self.track_height + 5
                y2 = y1 + self.track_height - 10

                self.canvas.coords(next_clip["rect_id"], x1, y1, x2, y2)
                self.canvas.coords(next_clip["left_handle"], x1 - 5, y1, x1 + 5, y2)
                self.canvas.coords(next_clip["right_handle"], x2 - 5, y1, x2 + 5, y2)
                self.canvas.coords(next_clip["text_id"], x1 + 5, (y1 + y2) / 2)

                # Reboucle pour résoudre overlap en chaîne
                self._resolve_overlaps_on_track(track_index)
                break  # très important pour éviter boucle infinie



    def delete_selected_clip(self, event=None):
        if not self._selected_clip:
            return

        clip = self._selected_clip

        # Supprime les éléments du canvas
        for key in ("rect_id", "text_id", "left_handle", "right_handle", "thumb_id"):
            if clip.get(key):
                self.canvas.delete(clip[key])

        # Supprime du tableau
        self.clips.remove(clip)

        # Callback si fourni
        if self.on_clip_removed:
            self.on_clip_removed(clip["object"])

        self._selected_clip = None
        self._reorder_background_clips()
        self.redraw()


    def get_background_image(self, time):
        for clip in self.clips:
            if( clip["track"] == "background" ):
                obj     = clip["object"]
                start    = obj.step.delay
                duration = obj.step.duration

                if( time >= start and time < start + duration ):
                    if( obj.is_ready() ):
                        return obj.get_image(time-start)
                    return self.on_video_update(obj,time-start)
                    #return obj.get_image(time-start)
