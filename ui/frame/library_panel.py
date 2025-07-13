import tkinter as tk
import ttkbootstrap as ttk
from ui.frame.scrollable_frame import ScrollableFrame


class VideoLibraryPanel(ttk.Frame):
    def __init__(self, parent, on_drop_callback=None, on_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_drop_callback = on_drop_callback
        self.on_click = on_click
        self._current_selected_frame = None
        self._added_video_paths = set()

        # Styles
        style = ttk.Style()
        style.configure("Selected.TFrame", relief="solid", borderwidth=2)
        style.configure("Unselected.TFrame", relief="flat", borderwidth=0)

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)

    def add_video(self, video):
        if video.path in self._added_video_paths:
            return
        self._added_video_paths.add(video.path)

        # Container
        container = ttk.Frame(self.scroll_frame.get_content_frame(), padding=5, style="Unselected.TFrame")
        container.pack(fill="x", padx=5, pady=2)

        # Thumbnail
        label_img = ttk.Label(container, image=video.thumb)
        label_img.image = video.thumb
        label_img.pack(side="left")

        # Texts
        text_frame = ttk.Frame(container)
        text_frame.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(text_frame, text=video.label, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(text_frame, text=video.path, font=("Segoe UI", 8), foreground="gray").pack(anchor="w")
        ttk.Label(text_frame, text=f"Durée : {video.step.duration}s", font=("Segoe UI", 8)).pack(anchor="w")

        # Bind all children recursively
        self._bind_all(container, video, container)

    def _bind_all(self, widget, video, top_frame):
        def on_click(event):
            self._select_frame(top_frame)
            if self.on_click:
                self.on_click(video)
            top_frame._drag_start_pos = (event.x_root, event.y_root)

        def on_motion(event):
            if not hasattr(top_frame, "_drag_start_pos"):
                return

            dx = abs(event.x_root - top_frame._drag_start_pos[0])
            dy = abs(event.y_root - top_frame._drag_start_pos[1])
            if dx > 5 or dy > 5:
                if not getattr(top_frame, "_is_dragging", False):
                    self._start_drag(video, top_frame, event)

                ghost = getattr(top_frame, "_ghost_label", None)
                if ghost:
                    ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")


        def on_release(event):
            self._end_drag(top_frame, event, video)

        widget.bind("<Button-1>", on_click)
        widget.bind("<B1-Motion>", on_motion)
        widget.bind("<ButtonRelease-1>", on_release)

        for child in widget.winfo_children():
            self._bind_all(child, video, top_frame)

    def _start_drag(self, video, widget, event):
        if getattr(widget, "_is_dragging", False):
            return

        widget._is_dragging = True
        ghost = tk.Toplevel()
        ghost.overrideredirect(True)
        ghost.attributes("-topmost", True)
        label = tk.Label(ghost, text=video.label, bg="#eeeeee", bd=1, relief="solid", font=("Arial", 10))
        label.pack()
        widget._ghost_label = ghost
        ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _end_drag(self, widget, event, video):
        print(f"_end_drag  {video.label}")
        if not getattr(widget, "_is_dragging", False):
            return
        print(f"_end_drag  {video.label}")

        ghost = getattr(widget, "_ghost_label", None)
        if ghost:
            ghost.destroy()
            widget._ghost_label = None

        widget._is_dragging = False
        if self.on_drop_callback:
            x, y = event.x_root, event.y_root
            dropped_on = self.winfo_containing(x, y)
            if hasattr(dropped_on, "_accepts_drop") and dropped_on._accepts_drop:
                self.on_drop_callback(video, x, y)

    def _select_frame(self, frame):
        if self._current_selected_frame:
            self._current_selected_frame.config(style="Unselected.TFrame")
        frame.config(style="Selected.TFrame")
        self._current_selected_frame = frame
