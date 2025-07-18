import tkinter as tk
import ttkbootstrap as ttk
from object.video import Video
from ui.frame.scrollable_frame import ScrollableFrame  # tu dois avoir cette classe déjà


class ClipLibrary(ttk.Frame):
    def __init__(self, parent, on_drop_callback=None, on_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_drop_callback = on_drop_callback
        self.on_click = on_click
        self._current_selected_frame = None
        self._added_video_paths = set()
        self._all_clips = []  # tous les clips, même filtrés
        self._current_filter = None

        # Layout : barre gauche + contenu droit
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="secondary.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self._create_sidebar_buttons()

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=1, sticky="nsew")

        # Styles
        style = ttk.Style()
        style.configure("Selected.TFrame", relief="solid", borderwidth=1)
        style.configure("Unselected.TFrame", relief="flat", borderwidth=0)
        style.configure("Hovered.TFrame", relief="ridge", borderwidth=1)


    def _create_sidebar_buttons(self):
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

    def has_video(self, path):
        return path in self._added_video_paths
    
    def add_unique_clip(self, clip):
        if( isinstance(clip, Video) ):
            if( clip.path in self._added_video_paths ):
                return
            new_clip = clip.clone()
            new_clip.step.delay = 0
            self._added_video_paths.add(clip.path)
        else:
            new_clip = clip.clone()
            new_clip.step.delay = 0
            new_clip.step.duration = 1

        self.add_clip(new_clip)

    def add_clip(self, clip):
        if( isinstance(clip, Video) ):
            if( clip.path in self._added_video_paths ):
                return
            self._added_video_paths.add(clip.path)

        self._all_clips.append(clip)

        if self._should_display(clip):
            if( isinstance(clip, Video) ):
                self._create_video_widget(clip)
            else:
                self._create_clip_widget(clip)

    def get_video(self, path):
        for clip in self._all_clips:
            if( isinstance(clip, Video) ):
                if clip.path == path:
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
                if( isinstance(clip, Video) ):
                    self._create_video_widget(clip)
                else:
                    self._create_clip_widget(clip)

    def _create_video_widget(self, clip):
        container = ttk.Frame(self.scroll_frame.get_content_frame(), padding=5, style="Unselected.TFrame")
        container.pack(fill="x", padx=5, pady=2)

        img = clip.get_thumb()
        label_img = ttk.Label(container, image=img)
        label_img.image = img
        label_img.pack(side="left")

        text_frame = ttk.Frame(container)
        text_frame.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(text_frame, text=clip.label, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(text_frame, text=clip.path, font=("Segoe UI", 8), foreground="gray").pack(anchor="w")
        ttk.Label(text_frame, text=f"Length : {clip.step.duration}s", font=("Segoe UI", 8)).pack(anchor="w")

        self._bind_all(container, clip, container)

    def _create_clip_widget(self, clip):
        container = ttk.Frame(self.scroll_frame.get_content_frame(), padding=5, style="Unselected.TFrame")
        container.pack(fill="x", padx=5, pady=2)

        text_frame = ttk.Frame(container)
        text_frame.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(text_frame, text=clip.label, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(text_frame, text=clip.__class__.__name__, font=("Segoe UI", 8), foreground="gray").pack(anchor="w")
        ttk.Label(text_frame, text=f"Length : {clip.step.duration}s", font=("Segoe UI", 8)).pack(anchor="w")
        self._bind_all(container, clip, container)

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
                top_frame.config(style="Hovered.TFrame")

        def on_leave(event):
            if top_frame != self._current_selected_frame:
                top_frame.config(style="Unselected.TFrame")


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

    def _select_frame(self, frame):
        if self._current_selected_frame:
            self._current_selected_frame.config(style="Unselected.TFrame")
        frame.config(style="Selected.TFrame")
        self._current_selected_frame = frame

    def reset(self):
        # Supprimer tous les widgets affichés
        for widget in self.scroll_frame.get_content_frame().winfo_children():
            widget.destroy()

        # Réinitialiser l'état interne
        self._all_clips.clear()
        self._added_video_paths.clear()
        self._current_selected_frame = None
        self._current_filter = None
        self._apply_filter("all")  # si tu veux forcer le filtre "Tous"

    def remove_focus(self):
        if self._current_selected_frame:
            self._current_selected_frame.config(style="Unselected.TFrame")
        
        