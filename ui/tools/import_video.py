
import os
import re
import subprocess
import threading
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.video import detect_and_cut_scenes



class ImportVideoTool:
    def __init__(self, state) :
        self.state = state

        # Crée la fenêtre Toplevel
        self.window = ttk.Toplevel()
        self.window.title("Import Video")

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
            text="Detect",
            bootstyle=SUCCESS,
            command=self.split_video,
            width=30
        )
        split_btn.pack(side='left', padx=15)

        # Label threshold
        threshold_label = ttk.Label(self.window, text="Scene threshold (0-1) :", font=("Arial", 12))
        threshold_label.pack(pady=(10, 0))
                
        self.threshold_var = ttk.DoubleVar(value=0.35)

        slider = ttk.Scale(
            self.window,
            from_=0,
            to=1,
            orient='horizontal',
            variable=self.threshold_var,
            command=self.update_threshold_label
        )
        slider.pack()

        self.threshold_label = ttk.Label(self.window, text=f"Seuil : {self.threshold_var.get():.2f}")
        self.threshold_label.pack()

        # Container pour les boutons d'action
        action_frame = ttk.Frame(self.window)
        action_frame.pack(pady=10)

        # Nouveau bouton Découper
        cut_btn = ttk.Button(
            action_frame,
            text="Split scenes",
            bootstyle=PRIMARY,
            command=self.cut_video_from_ui,
            width=30
        )
        cut_btn.pack(side='left', padx=15)

        
        # Nouveau bouton Découper
        cut_btn = ttk.Button(
            action_frame,
            text="Split Interval (6sec)",
            bootstyle=PRIMARY,
            command=self.cut_video_by_interval,
            width=30
        )
        cut_btn.pack(side='left', padx=15)

        # Load config
        self.split_entry.delete(0, 'end')
        self.split_entry.insert(0, self.state["config"]["downloader"].get("split", ""))

        # Zone de log
        self.log_text = ttk.Text(self.window, height=8, wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)

    def update_threshold_label(self, event=None):
        value = self.threshold_var.get()
        self.threshold_label.config(text=f"Seuil : {value:.2f}")


    def log_message(self, message):
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')


    def split_video(self):
        def thread_func():
            threshold = self.threshold_var.get()
            self.detect_scene_cuts(
                self.split_entry.get().strip(),
                threshold
            )
            #"C:\\PYGAME\\clips"  # TODO: rendre dynamique

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()
        self.check_thread(thread)


    def check_thread(self, thread):
        if thread.is_alive():
            self.state['app'].after(100, lambda: self.check_thread(thread))
        else:
            # TODO: refresh thumbs si nécessaire
            pass


    def detect_scene_cuts(self, path, scene_threshold=0.35):
        if not os.path.isfile(path):
            self.log_message(f"[ERREUR] Fichier introuvable: {path}")
            return []

        temp_log = "scene_changes.txt"

        try:
            subprocess.run([
                "ffmpeg", "-i", path,
                "-filter_complex", f"select='gt(scene,{scene_threshold})',showinfo",
                "-f", "null", "-"
            ], stderr=open(temp_log, "w", encoding="utf-8"), stdout=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError:
            self.log_message("[ERREUR] Échec de l'exécution de ffmpeg pour détecter les cuts.")
            return []

        timestamps = []
        if os.path.exists(temp_log):
            with open(temp_log, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r"pts_time:(\d+(\.\d+)?)", line)
                    if match:
                        timestamps.append(float(match.group(1)))
        else:
            self.log_message("[ERREUR] Le fichier scene_changes.txt est manquant.")
            return []

        # # ➜ Si aucun cut : récupérer la durée totale
        # if not timestamps:
        #     try:
        #         result = subprocess.run([
        #             "ffprobe", "-v", "error",
        #             "-show_entries", "format=duration",
        #             "-of", "default=noprint_wrappers=1:nokey=1",
        #             path
        #         ], capture_output=True, text=True, check=True)
        #         duration = float(result.stdout.strip())
        #         self.log_message(f"[INFO] Aucun cut détecté → vidéo complète : 0 → {duration:.2f}s")
        #         return [0.0, duration]
        #     except subprocess.CalledProcessError:
        #         self.log_message("[ERREUR] Impossible de lire la durée de la vidéo.")
        #         return []

        self.log_message(f"[OK] {len(timestamps)} cuts détectés : {timestamps}")
        return timestamps


    def select_video_file(self):
        filepath = filedialog.askopenfilename(
            title="Choisir un fichier vidéo",
            filetypes=[("Fichiers vidéo", "*.mp4 *.mov *.avi *.mkv"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.split_entry.delete(0, 'end')
            self.split_entry.insert(0, filepath)


    def on_close(self):
        # Met à jour la config
        self.state["config"]["downloader"]["split"] = self.split_entry.get()

        # Détruire la fenêtre
        self.window.destroy()

    
    def cut_video_by_interval(self):
        video_path = self.split_entry.get().strip()

        if not video_path:
            self.log_message("[ERREUR] Aucun fichier vidéo sélectionné.")
            return

        # Appelle ta logique de découpe ici :
        self.cut_and_save_clips(video_path, [], interval=6)

    def cut_video_from_ui(self):
        video_path = self.split_entry.get().strip()
        threshold = self.threshold_var.get()

        if not video_path:
            self.log_message("[ERREUR] Aucun fichier vidéo sélectionné.")
            return

        timestamps = self.detect_scene_cuts(video_path, scene_threshold=threshold)

        if not timestamps:
            self.log_message("[INFO] Aucun cut détecté, la vidéo sera copiée telle quelle.")
        else:
            self.log_message(f"[INFO] Découpage en {len(timestamps)} segments.")

        # Appelle ta logique de découpe ici :
        self.cut_and_save_clips(video_path, timestamps)

    def cut_and_save_clips(self, video_path, timestamps, interval=0):
        # Vérifie toujours la durée
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], capture_output=True, text=True)

        try:
            duration = float(result.stdout.strip())
        except:
            self.log_message("[ERREUR] Impossible de lire la durée de la vidéo.")
            return
        
        # On decoupe tous les X secondes
        if( interval > 0 ):
            time = interval
            while( duration > time ):
                timestamps.append(time)
                time += interval

        # TOUJOURS construire [0, CUTS..., END]
        if not timestamps:
            timestamps = [0.0, duration]
        else:
            timestamps = [0.0] + timestamps + [duration]

        self.log_message(f"[INFO] Segments : {timestamps}")

        base_dir = "C:\\PYGAME\\clips"
        output_dir = os.path.join(base_dir, os.path.basename(video_path)[:-4])
        os.makedirs(output_dir, exist_ok=True)

        EPSILON = 0.001  # 1 ms

        for i in range(len(timestamps) - 1):
            start = timestamps[i]
            end = timestamps[i + 1]
            length = end - start

            # Pour éviter chevauchement : raccourcir légèrement sauf le dernier segment
            if i < len(timestamps) - 2:
                length -= EPSILON
            
            output_file = os.path.join(output_dir, f"clip_{i}.mp4")

            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", video_path,
                    "-ss", str(start), "-t", str(length),
                    "-vf", "scale=w=608:h=1080:force_original_aspect_ratio=increase,crop=608:1080",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "aac", output_file
                ], check=True)
                self.log_message(f"[OK] Clip_{i} exporté ({length:.2f}s)")
            except subprocess.CalledProcessError:
                self.log_message(f"[ERREUR] Échec du clip_{i}")

            #"-c:v", "libx264", "-preset", "medium", "-crf", "23",
            #"-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",