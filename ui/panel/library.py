import json
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from object.object import Object
from object.sound import Sound
from object.video import Video
from ui.frame.parameter_form import ParameterForm
from ui.frame.scrollable_frame import ScrollableFrame
from ui.frame.type_chooser import TypeChooser  # tu dois avoir cette classe déjà

from concurrent.futures import ThreadPoolExecutor, wait

from ui.log import log_message

class LibraryPanel(ttk.Frame):
    def __init__(self, state, parent, on_drop_callback=None, on_click=None, on_clip_ready=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = state
        self.on_drop_callback = on_drop_callback
        self.on_click = on_click
        self._current_selected_frame = None
        self._all_clips = []  # tous les clips, même filtrés
        self._current_filter = None
        self.on_clip_ready = on_clip_ready

        # Layout : barre gauche + contenu droit
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="secondary.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self._create_sidebar_buttons()

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=1, sticky="nsew")

        self.bind_all("<Delete>", self.delete_selected_clip)
        self.update_idletasks()
        self.update()


    def delete_selected_clip(self, event=None):
        if( self._current_selected_frame is None):
            return
        
        clip = self._current_selected_frame.clip

        if( self.state["game"].has_object_with_uid(clip.uid) ):
            messagebox.showerror("Error", "This clip is in use in the timeline")
            return            
        
        if clip in self._all_clips:
            self._all_clips.remove(clip)
            
        self._current_selected_frame.destroy()
        self._current_selected_frame = None

        self.clear_selection()
        
    def clear_selection(self):
        if self._current_selected_frame is not None:
            self._apply_style_to_container(self._current_selected_frame, "Unselected")
            self._apply_selection_border(self._current_selected_frame, False)
            self._current_selected_frame = None


    ############################################

    def get_subclasses(self, cls):
        subclasses = set()
        work = [cls]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
        return subclasses

    ######################################

    def open_parameter_form(self, cls):
        def on_submit(result):
            data = {
                "type": cls.__name__,
                "label": f"New {cls.__name__}"
            }
            # On ajoute chaque section dans data
            for key, value in result.items():
                data[key] = value

            object = self.state["game"].create_object(data)
            if( isinstance(object, Sound) ):
                object.step.duration = object.sound.sound.get_length()
            elif( isinstance(object, Video) ):
                pass
            else:
                object.step.duration = 1
            self.add_clip(object)

        fields = cls.parameter_fields()
        ParameterForm(self.state["app"], fields, on_submit)



    def open_type_chooser(self):
        def handle_choice(choice):
                    
            subclasses = self.get_subclasses(Object)
            cls_dict = {cls.__name__: cls for cls in subclasses}
            cls = cls_dict[choice]

            if hasattr(cls, "parameter_fields"):
                self.open_parameter_form(cls)
            else:
                # fallback : objet avec données par défaut
                data = {
                    "type": choice,
                    "label": f"New {choice}",
                    "step": {"duration": 2}
                }
                object = self.state["game"].create_object(data)
                self.add_clip(object)
                

        subclasses = self.get_subclasses(Object)
        type_list = sorted([cls.__name__ for cls in subclasses])
        TypeChooser(self.state["app"], type_list, handle_choice)



    def _create_sidebar_buttons(self):

        #Add button
        btn = ttk.Button(
                self.sidebar,
                text="+",
                width=4,
                command=lambda: self.open_type_chooser(),
                style="Tool.TButton"
            )
        btn.pack(pady=4)

        btn_sort = ttk.Button(
            self.sidebar,
            text="🔤",
            width=4,
            command=self.sort_by_label,
            style="Tool.TButton"
        )
        btn_sort.pack(pady=4)


        filters = [
            ("all", "🧩", "Tous"),
            ("video", "🎥", "Vidéos"),
            ("textSurface", "📝", "Texte Surface"),
            ("textDraw", "📝", "Texte Draw"),
            ("image", "🖼️", "Images"),
        ]

        for ftype, emoji, label in filters:
            btn = ttk.Button(
                self.sidebar,
                text=emoji,
                width=4,
                command=lambda t=ftype: self._apply_filter(t),
                style="Tool.TButton"
            )
            btn.pack(pady=4)

    def sort_by_label(self):
        self._all_clips.sort(key=lambda clip: clip.label.lower())
        self.refresh_display()


    def add_clip(self, clip):

        if( isinstance(clip, Sound) and clip.step.duration == -1 and clip.sound.sound.get_length() > 0 ):
            clip.step.duration = clip.sound.sound.get_length()
            
        self._all_clips.append(clip)

        if self._should_display(clip):
            self._create_clip_widget_with_thumb(clip)

    def refresh_display(self):
        self._current_selected_frame = None

        # Supprimer tous les widgets affichés
        for widget in self.scroll_frame.get_content_frame().winfo_children():
            widget.destroy()

        # Réafficher tous les clips dans l'ordre actuel de self._all_clips
        for clip in self._all_clips:
            if self._should_display(clip):
                self._create_clip_widget_with_thumb(clip)

    def get_clip_by_uid(self, uid):
        for clip in self._all_clips:
            if clip.uid == uid:
                return clip
        return None

    def _should_display(self, clip):
        if self._current_filter in (None, "all"):
            return True
        return getattr(clip, "type", "N/A") == self._current_filter

    def _apply_filter(self, filter_type):
        self._current_filter = filter_type

        for widget in self.scroll_frame.get_content_frame().winfo_children():
            widget.destroy()

        for clip in self._all_clips:
            if self._should_display(clip):
                self._create_clip_widget_with_thumb(clip)


    def _update_thumb_image(self, label_widget, clip, length_var):
        length_var.set(f"Length : {round(clip.step.duration, 2)}s")
        thumb = clip.get_thumb()
        label_widget.config(image=thumb)
        label_widget.image = thumb 


    def _create_clip_widget_with_thumb(self, clip):
        # Frame principale (pour la bordure)
        #outer_frame = ttk.Frame(self.scroll_frame.get_content_frame(),style="Border.TFrame",padding=1)

        outer_frame = tk.Frame( self.scroll_frame.get_content_frame(),
                                highlightthickness=0,
                                bd=0)

        outer_frame.pack(fill="x", padx=5, pady=5)
        outer_frame.update_idletasks()
        
        # Frame interne (pour le fond coloré)
        inner_frame = ttk.Frame(outer_frame,style="Unselected.TFrame", padding=3 )
        inner_frame.pack(fill="both", expand=True)

        img = clip.get_thumb()
        label_img = ttk.Label(inner_frame, image=img,  style="Unselected.TLabel")
        label_img.image = img
        label_img.pack(side="left", padx=(0,5))

        # Créez un conteneur spécial pour les références
        class LabelHolder:
            pass

        holder = LabelHolder()
        holder.length_var = tk.StringVar(value=f"Length : {round(clip.step.duration, 2)}s")
        
        # Enregistre le callback pour MAJ plus tard
        def on_thumb_ready():
            self.after(0, lambda: self._update_thumb_image(label_img, clip, holder.length_var))
        if( img is None ):
            clip.on_thumb_ready_callbacks.append(on_thumb_ready)
        else:
            on_thumb_ready()

        ttk.Label(inner_frame, text=clip.label, font=("Segoe UI", 10, "bold"), style="Unselected.TLabel").pack(anchor="w")
        ttk.Label(inner_frame, text=clip.get_description(), font=("Segoe UI", 8), foreground="gray", style="Unselected.TLabel").pack(anchor="w")
        ttk.Label(inner_frame, textvariable=holder.length_var, font=("Segoe UI", 8), style="Unselected.TLabel").pack(anchor="w")

        # Save clip reference
        outer_frame.clip = clip
        outer_frame.inner_frame = inner_frame
        outer_frame.label_holder = holder
        self._bind_all(outer_frame, clip, outer_frame)
            
  
            
    def start_lazy_loading(self):
        #TODO: I have 2 fonctions available (sequencially or parallely), same performances...
        threading.Thread(target=self._load_videos_sequentially, args=(), daemon=True).start()


    def _on_video_ready(self, object):
        print(f"Video {object.path} ready")
        if( self.on_clip_ready ):
            self.on_clip_ready(object)

    def _load_videos_sequentially(self):
        start_time = time.time()
        for object in self._all_clips:
            if isinstance(object, Video) and object.path:
                object.load()
                object.on_ready_callbacks.append(self._on_video_ready)
                while not object.is_ready():
                    time.sleep(0.1)
        end_time = time.time()
        print(f"All videos loaded in {end_time - start_time:.2f} seconds")


    def _load_videos_in_parallel(self):
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for obj in self._all_clips:
                if isinstance(obj, Video) and obj.path:
                    futures.append(executor.submit(self._load_async_data, obj))

            # Attendre que toutes les vidéos soient chargées
            wait(futures)

        end_time = time.time()
        print(f"All videos loaded in {end_time - start_time:.2f} seconds")



    def _load_videos_in_parallel_basic(self):
        for obj in self._all_clips:
            if isinstance(obj, Video) and obj.path:
                threading.Thread(target=self._load_async_data, args=(obj,), daemon=True).start()

    def _load_async_data(self, object):
        object.load()
        object.on_ready_callbacks.append(self._on_video_ready)
        while not object.is_ready():
            time.sleep(0.1)


    def _bind_all(self, widget, clip, top_frame):
        
        def on_click(event):
            self._select_frame(top_frame)
            if self.on_click:
                self.on_click(clip)
            top_frame._drag_start_pos = (event.x_root, event.y_root)

        def on_motion(event):
            if not hasattr(top_frame, "_drag_start_pos"):
                return

            dx = abs(event.x_root - top_frame._drag_start_pos[0])
            dy = abs(event.y_root - top_frame._drag_start_pos[1])
            if dx > 5 or dy > 5:
                if not getattr(top_frame, "_is_dragging", False):
                    self._start_drag(clip, top_frame, event)

                ghost = getattr(top_frame, "_ghost_label", None)
                if ghost:
                    ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        def on_release(event):
            self._end_drag(top_frame, event, clip)

        def on_enter(event):
            if top_frame != self._current_selected_frame:
                self._apply_style_to_container(top_frame, "Hovered")

        def on_leave(event):
            if top_frame != self._current_selected_frame:
                self._apply_style_to_container(top_frame, "Unselected")


        widget.bind("<Button-1>", on_click)
        widget.bind("<B1-Motion>", on_motion)
        widget.bind("<ButtonRelease-1>", on_release)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

        for child in widget.winfo_children():
            self._bind_all(child, clip, top_frame)

    def _start_drag(self, clip, widget, event):
        if getattr(widget, "_is_dragging", False):
            return

        widget._is_dragging = True
        ghost = tk.Toplevel()
        ghost.overrideredirect(True)
        ghost.attributes("-topmost", True)
        label = tk.Label(ghost, text=clip.label, bg="#eeeeee", bd=1, relief="solid", font=("Arial", 10))
        label.pack()
        widget._ghost_label = ghost
        ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _end_drag(self, widget, event, clip):
        if not getattr(widget, "_is_dragging", False):
            return

        ghost = getattr(widget, "_ghost_label", None)
        if ghost:
            ghost.destroy()
            widget._ghost_label = None

        widget._is_dragging = False
        if self.on_drop_callback:
            x, y = event.x_root, event.y_root
            dropped_on = self.winfo_containing(x, y)
            if hasattr(dropped_on, "_accepts_drop") and dropped_on._accepts_drop:
                self.on_drop_callback(clip, x, y)

    def _apply_selection_border(self, frame, selected: bool):
        # Appliquer ou supprimer la bordure fine
        if isinstance(frame, tk.Frame):
            if selected:
                frame.config(highlightthickness=1, highlightbackground=self.state["colors"]["selected_border"])
            else:
                frame.config(highlightthickness=0)

    def _select_frame(self, frame):
        if self._current_selected_frame:
            self._apply_style_to_container(self._current_selected_frame, "Unselected")
            self._apply_selection_border(self._current_selected_frame, False)

        self._apply_style_to_container(frame, "Selected")
        self._apply_selection_border(frame, True)
        self._current_selected_frame = frame



    def _apply_style_to_container(self, frame, style_state: str):
        """
        Applique le style visuel (Selected, Unselected, Hovered) à un clip container.

        Args:
            frame: le tk.Frame parent (outer_frame)
            style_state: "Selected", "Unselected" ou "Hovered"
        """
        if hasattr(frame, "inner_frame"):
            inner = frame.inner_frame
            for child in inner.winfo_children():
                if isinstance(child, ttk.Label):
                    label_style = f"{style_state}.TLabelBold" if "bold" in child.winfo_name().lower() else f"{style_state}.TLabel"
                    child.configure(style=label_style)

            # Appliquer le style sur le inner_frame
            inner.configure(style=f"{style_state}.TFrame")



    def reset(self):
        # Supprimer tous les widgets affichés
        for widget in self.scroll_frame.get_content_frame().winfo_children():
            widget.destroy()

        # Réinitialiser l'état interne
        self._all_clips.clear()
        self._current_selected_frame = None
        self._current_filter = None
        self._apply_filter("all")  # si tu veux forcer le filtre "Tous"

    def remove_focus(self):
        """Désélectionne l'élément actuellement sélectionné (s'il existe)."""
        if self._current_selected_frame is not None:
            self._apply_style_to_container(self._current_selected_frame, "Unselected")
            self._apply_selection_border(self._current_selected_frame, False)
            self._current_selected_frame = None

            