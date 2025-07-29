
import os
import re
import subprocess
import threading
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.download import download_video
from ui.log import log_message



def detect_and_cut_scenes(state, input_path, output_base_dir):
    if not os.path.isfile(input_path):
        log_message(state, f"[ERREUR] Fichier introuvable : {input_path}")
        return

    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)

    video_name = os.path.basename(input_path)
    base_name = os.path.splitext(video_name)[0]
    output_dir = os.path.join(output_base_dir, base_name)[:50]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_message(state, f"Analysing: {video_name}...")

    # Étape 1 : Détection des cuts avec ffmpeg
    try:
        with open("scene_changes.txt", "w", encoding="utf-8") as log_file:
            subprocess.run([
                "ffmpeg", "-i", input_path,
                "-filter_complex", "select='gt(scene,0.35)',showinfo",
                "-f", "null", "-"
            ], stderr=log_file, stdout=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        log_message(state, "[ERROR] Échec de l'exécution de ffmpeg.")
        return

    if not os.path.exists("scene_changes.txt"):
        log_message(state, "[ERROR] Le fichier scene_changes.txt est manquant.")
        return

    # Étape 2 : Lecture des timestamps
    timestamps = []
    with open("scene_changes.txt", "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"pts_time:(\d+(\.\d+)?)", line)
            if match:
                timestamps.append(float(match.group(1)))

    # Étape 3 : Récupération de la durée totale
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ], capture_output=True, text=True)

    try:
        duration = float(result.stdout.strip())
    except:
        log_message(state, "[ERREUR] Unable to read video duration.")
        return

    if not timestamps:
        log_message(state, f"No cuts detected, will convert the whole video.")
    
    # Forcer découpe « 1 clip » si aucun cut détecté :
    timestamps = [0.0] + timestamps + [duration]

    log_message(state, f"[{len(timestamps)-1}] segments to generate.")

    # Étape 4 : Découpe des scènes
    log_message(state, "Cut, scale and crop in progress...")
    for i in range(len(timestamps) - 1):
        start = timestamps[i]
        end = timestamps[i + 1]
        length = end - start

        output_file = os.path.join(output_dir, f"clip_{i}.mp4")
        log_message(state, f"Working on Clip [{i+1}/{len(timestamps)-1}], Start={start:.2f}s, Duration={length:.2f}s")

        try:
            subprocess.run([
                "ffmpeg", "-i", input_path,
                "-ss", str(start), "-t", str(length),
                "-vf", "scale=w=608:h=1080:force_original_aspect_ratio=increase,crop=608:1080",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-c:a", "aac", output_file
            ], check=True)
        except subprocess.CalledProcessError:
            log_message(state, f"[ERROR] Échec de la découpe du segment {i}")

    log_message(state, f"Done for : {video_name}")




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

       