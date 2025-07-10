
import threading
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.download import download_video
from ui.video import detect_and_cut_scenes

class DownloaderWindow:
    def __init__(self, state) :
        self.state = state

        # Crée la fenêtre Toplevel
        self.window = ttk.Toplevel()
        self.window.title("Downloader")

        # Définir la taille souhaitée
        window_width = 600
        window_height = 300

        # Obtenir la taille de l'écran
        screen_width = self.state['app'].winfo_screenwidth()
        screen_height = self.state['app'].winfo_screenheight()

        # Calculer les coordonnées
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Appliquer la géométrie centrée
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")


        # Gestion de la fermeture
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Téléchargement
        url_label = ttk.Label(self.window, text="Colle l'URL YouTube ou TikTok :", font=("Arial", 12))
        url_label.pack(pady=5)

        container = ttk.Frame(self.window)
        container.pack(pady=5, padx=20, fill='x')

        self.url_entry = ttk.Entry(container, width=50)
        self.url_entry.pack(side='left', expand=True, fill='x')

        download_btn = ttk.Button(
            container,
            text="Télécharger",
            bootstyle=SUCCESS,
            command=self.download_video_threaded,
            width=30
        )
        download_btn.pack(side='left', padx=15)

        # Split
        split_label = ttk.Label(self.window, text="Split video in clips :", font=("Arial", 12))
        split_label.pack(pady=5)

        container_split = ttk.Frame(self.window)
        container_split.pack(pady=5, padx=20, fill='x')

        select_btn = ttk.Button(
            container_split,
            text="Open",
            command=self.select_video_file
        )
        select_btn.pack(side='left', fill='x')

        self.split_entry = ttk.Entry(container_split, width=40)
        self.split_entry.pack(side='left', expand=True, fill='x')

        split_btn = ttk.Button(
            container_split,
            text="Split",
            bootstyle=SUCCESS,
            command=self.split_video,
            width=30
        )
        split_btn.pack(side='left', padx=15)

        # Load config
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, self.state["config"]["downloader"].get("url", ""))
        self.split_entry.delete(0, 'end')
        self.split_entry.insert(0, self.state["config"]["downloader"].get("split", ""))

    def select_video_file(self):
        filepath = filedialog.askopenfilename(
            title="Choisir un fichier vidéo",
            filetypes=[("Fichiers vidéo", "*.mp4 *.mov *.avi *.mkv"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.split_entry.delete(0, 'end')
            self.split_entry.insert(0, filepath)

    def download_video_threaded(self):
        threading.Thread(
            target=download_video,
            args=(self.state, self.url_entry, self.split_entry),
            daemon=True
        ).start()

    def split_video(self):
        def thread_func():
            detect_and_cut_scenes(
                self.state,
                self.split_entry.get().strip(),
                "C:\\PYGAME\\clips"  # TODO: rendre dynamique
            )

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()
        self.check_thread(thread)

    def check_thread(self, thread):
        if thread.is_alive():
            self.state['app'].after(100, lambda: self.check_thread(thread))
        else:
            # TODO: refresh thumbs si nécessaire
            pass
        
    def on_close(self):
        # Met à jour la config
        self.state["config"]["downloader"]["url"]   = self.url_entry.get()
        self.state["config"]["downloader"]["split"] = self.split_entry.get()

        # Détruire la fenêtre
        self.window.destroy()

       