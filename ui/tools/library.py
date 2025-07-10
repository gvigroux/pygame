import os
import threading
import queue
from tkinter import filedialog
import cv2
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import vlc

from ui.log import log_message

VIDEO_EXTENSIONS = [".mp4", ".avi"]
THUMBNAIL_SIZE = (160, 90)

class LibraryWindow:
    def __init__(self, state):
        self.state = state
        self.current_player = None
        self.current_video_frame = None
        self.thumbs = []
        self.thumbnail_queue = queue.Queue()

        # Crée la fenêtre Toplevel
        self.window = ttk.Toplevel()
        self.window.title("Library")

        
        # Définir la taille souhaitée
        window_width = 1000
        window_height = 700

        # Obtenir la taille de l'écran
        screen_width = self.state['app'].winfo_screenwidth()
        screen_height = self.state['app'].winfo_screenheight()

        # Calculer les coordonnées
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Appliquer la géométrie centrée
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Colonne gauche : Canvas + scrollbar
        left_side = ttk.Frame(self.window)
        left_side.pack(side="left", fill="both", expand=True)

        self.thumbs_canvas = ttk.Canvas(left_side)
        scrollbar = ttk.Scrollbar(left_side, orient="vertical", command=self.thumbs_canvas.yview)

        self.scrollable_frame = ttk.Frame(self.thumbs_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumbs_canvas.configure(scrollregion=self.thumbs_canvas.bbox("all"))
        )
        def _on_mousewheel(event):
            self.thumbs_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.thumbs_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.thumbs_canvas.bind_all("<Button-4>", lambda e: self.thumbs_canvas.yview_scroll(-1, "units"))
        self.thumbs_canvas.bind_all("<Button-5>", lambda e: self.thumbs_canvas.yview_scroll(1, "units"))

        self.thumbs_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.thumbs_canvas.configure(yscrollcommand=scrollbar.set)

        self.thumbs_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Colonne droite : vidéo
        self.video_frame = ttk.Frame(self.window, width=304, height=540)
        self.video_frame.pack(side="right", padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        video_label = ttk.Label(self.video_frame)
        video_label.pack(expand=True)

        # Lance le thread de génération
        self.start_thumbnail_loader("C:\\PYGAME\\clips")

    def start_thumbnail_loader(self, video_dir):
        thread = threading.Thread(target=self.load_thumbnails, args=(video_dir,), daemon=True)
        thread.start()
        self.check_queue()

    def load_thumbnails(self, video_dir):
        video_files = self.get_all_video_files(video_dir)
        log_message(self.state, f"Found {len(video_files)} videos.")
        for video_path in video_files:
            thumb = self.extract_thumbnail(video_path)
            if thumb:
                self.thumbnail_queue.put((thumb, video_path))

    def check_queue(self):
        try:
            while True:
                thumb, video_path = self.thumbnail_queue.get_nowait()
                self.add_thumbnail(thumb, video_path)
        except queue.Empty:
            pass
        self.window.after(100, self.check_queue)

    def add_thumbnail(self, thumb, video_path, columns=8):
        self.thumbs.append(thumb)  # Garde la référence pour éviter le GC

        i = len(self.thumbs) - 1
        row = i // columns
        col = i % columns

        frame = ttk.Frame(self.scrollable_frame, padding=5)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nw")

        label_img = ttk.Label(frame, image=thumb)
        label_img.image = thumb
        label_img.pack()

        label_img.bind("<Button-1>", lambda e, path=video_path: self.play_video_vlc(self.state, path))

        label_text = ttk.Label(frame, text=os.path.basename(video_path), wraplength=150)
        label_text.pack()

    def get_all_video_files(self, directory):
        video_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                    video_files.append(os.path.join(root, file))
        return video_files

    def extract_thumbnail(self, video_path):
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()
        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail(THUMBNAIL_SIZE)
            return ImageTk.PhotoImage(img)
        return None

    def play_video_vlc(self, state, video_path):
        log_message(state, f"Play video [{video_path}]")
        if self.current_player is not None:
            self.current_player.stop()
            self.current_player.release()
            self.current_player = None
        if self.current_video_frame is not None:
            self.current_video_frame.destroy()
            self.current_video_frame = None

        self.current_video_frame = ttk.Frame(self.video_frame, width=304, height=540)
        self.current_video_frame.pack()

        instance = vlc.Instance()
        player = instance.media_player_new()

        handle = self.current_video_frame.winfo_id()
        media = instance.media_new(video_path)
        player.set_media(media)
        player.set_hwnd(handle)  # Windows

        player.play()
        self.current_player = player

    def on_close(self):
        self.window.destroy()
