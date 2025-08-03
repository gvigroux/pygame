
import os
import re
import subprocess
import threading
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import queue
from concurrent.futures import ThreadPoolExecutor

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

        self.extract_audio_var = ttk.BooleanVar(value=False)
        extract_audio_check = ttk.Checkbutton(
            self.window,
            text="Extraire le son en MP3 pour chaque clip",
            variable=self.extract_audio_var,
            bootstyle="success"
        )
        extract_audio_check.pack(pady=(5, 10))


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

        self.log_message("Analyzing video...")

        cmd = [
            "ffmpeg", "-i", path,
            "-filter_complex", f"select='gt(scene,{scene_threshold})',showinfo",
            "-f", "null", "-"
        ]
        
        # Exécution avec capture des logs
        return_code = self.run_ffmpeg_command(cmd, "[FFmpeg] ")
        if return_code != 0:
                self.log_message("[ERREUR] Échec de la détection des scènes")
                return []

        # try:
        #     subprocess.run([
        #         "ffmpeg", "-i", path,
        #         "-filter_complex", f"select='gt(scene,{scene_threshold})',showinfo",
        #         "-f", "null", "-"
        #     ], stderr=open(temp_log, "w", encoding="utf-8"), stdout=subprocess.DEVNULL, check=True)
        # except subprocess.CalledProcessError:
        #     self.log_message("[ERREUR] Échec de l'exécution de ffmpeg pour détecter les cuts.")
        #     return []

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

        self.log_message(f"[OK] {len(timestamps)} cut(s) detected : {timestamps}")
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
            self.log_message("[ERROR] No video selected.")
            return

        # Appelle ta logique de découpe ici :
        self.cut_and_save_clips(video_path, [], interval=6)

    def cut_video_from_ui(self):
        video_path = self.split_entry.get().strip()
        threshold = self.threshold_var.get()

        if not video_path:
            self.log_message("[ERROR] No video selected.")
            return

        timestamps = self.detect_scene_cuts(video_path, scene_threshold=threshold)

        if not timestamps:
            self.log_message("[INFO] Aucun cut détecté, la vidéo sera copiée telle quelle.")
        else:
            self.log_message(f"[INFO] Découpage en {len(timestamps)} segments.")

        # Appelle ta logique de découpe ici :
        self.cut_and_save_clips(video_path, timestamps)

    # def cut_and_save_clipsOLD(self, video_path, timestamps, interval=0):
    #     # Vérifie toujours la durée
    #     result = subprocess.run([
    #         "ffprobe", "-v", "error",
    #         "-show_entries", "format=duration",
    #         "-of", "default=noprint_wrappers=1:nokey=1",
    #         video_path
    #     ], capture_output=True, text=True)

    #     try:
    #         duration = float(result.stdout.strip())
    #     except:
    #         self.log_message("[ERROR] Unable to read video duration.")
    #         return
        
    #     # On decoupe tous les X secondes
    #     if( interval > 0 ):
    #         time = interval
    #         while( duration > time ):
    #             timestamps.append(time)
    #             time += interval

    #     # TOUJOURS construire [0, CUTS..., END]
    #     if not timestamps:
    #         timestamps = [0.0, duration]
    #     else:
    #         timestamps = [0.0] + timestamps + [duration]

    #     self.log_message(f"[INFO] Segments : {timestamps}")

    #     base_dir = "C:\\PYGAME\\clips"
    #     output_dir = os.path.join(base_dir, os.path.basename(video_path)[:-4])
    #     os.makedirs(output_dir, exist_ok=True)

    #     EPSILON = 0.001  # 1 ms

    #     for i in range(len(timestamps) - 1):
    #         start = timestamps[i]
    #         end = timestamps[i + 1]
    #         length = end - start

    #         # Pour éviter chevauchement : raccourcir légèrement sauf le dernier segment
    #         if i < len(timestamps) - 2:
    #             length -= EPSILON
            
    #         output_file = os.path.join(output_dir, f"clip_{i:03}.mp4")

          
    #         cmd = [
    #             "ffmpeg", "-y", "-i", video_path,
    #             "-ss", str(start), "-t", str(length),
    #             "-vf", "scale=w=608:h=1080:force_original_aspect_ratio=increase,crop=608:1080",
    #             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
    #             "-c:a", "aac", output_file
    #         ]
    #         self.log_message(f"Starting to create Clip_{i:03}")
    #         return_code = self.run_ffmpeg_command(cmd, f"[Clip {i:03}] ")
    #         if return_code == 0:
    #             self.log_message(f"[OK] Clip {i:03} créé ({length:.2f}s)")
    #             if self.extract_audio_var.get():
    #                 self.extract_audio(video_path, start, length, output_file, i)
    #         else:
    #             self.log_message(f"[ÉCHEC] Clip {i:03} non créé")


                
            #  try:
            #     subprocess.run([
            #         "ffmpeg", "-y", "-i", video_path,
            #         "-ss", str(start), "-t", str(length),
            #         "-vf", "scale=w=608:h=1080:force_original_aspect_ratio=increase,crop=608:1080",
            #         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            #         "-c:a", "aac", output_file
            #     ], check=True)
            #     self.log_message(f"Clip_{i:03} created ({length:.2f}s)")

            #     if self.extract_audio_var.get():
            #         audio_file = os.path.join(output_dir, f"clip_{i:03}.mp3")
            #         try:
            #             subprocess.run([
            #                 "ffmpeg", "-y", "-i", video_path,
            #                 "-ss", str(start), "-t", str(length),
            #                 "-vn",  # pas de vidéo
            #                 "-acodec", "libmp3lame",
            #                 "-q:a", "2",  # qualité élevée (1 = meilleure)
            #                 audio_file
            #             ], check=True)
            #             self.log_message(f"Audio MP3 created : clip_{i:03}.mp3")
            #         except subprocess.CalledProcessError:
            #             self.log_message(f"[ERROR] Unable to process audio clip_{i:03}")

            # except subprocess.CalledProcessError:
            #     self.log_message(f"[ERROR] clip_{i:03}")


    def extract_audio(self, video_path, start_time, duration, output_dir, clip_index):
        """
        Extrait l'audio d'un segment vidéo en MP3
        Args:
            video_path (str): Chemin du fichier vidéo source
            start_time (float): Début du segment (en secondes)
            duration (float): Durée du segment (en secondes)
            output_dir (str): Dossier de sortie
            clip_index (int): Numéro du clip pour les logs
        """
        audio_filename = f"clip_{clip_index:03d}.mp3"
        output_path = os.path.join(output_dir, audio_filename)
        
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite sans demander
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration),
            "-vn",  # Pas de vidéo
            "-acodec", "libmp3lame",
            "-q:a", "2",  # Qualité audio (2 = très bon, 0 = meilleur)
            "-map_metadata", "-1",  # Supprime les métadonnées
            output_path
        ]

        self.log_message(f"[Audio {clip_index}] Extraction en cours...")
        
        try:
            # Utilisez votre méthode run_ffmpeg_command existante
            return_code = self.run_ffmpeg_command(cmd, f"[Audio {clip_index}] ")
            
            if return_code == 0:
                self.log_message(f"[SUCCÈS] Audio {clip_index} sauvegardé: {audio_filename}")
                return True
            else:
                self.log_message(f"[ÉCHEC] Erreur lors de l'extraction audio {clip_index}")
                return False
                
        except Exception as e:
            self.log_message(f"[ERREUR CRITIQUE] Audio {clip_index}: {str(e)}")
            return False
        
        
    def run_ffmpeg_command(self, command, log_prefix=""):
        process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8'
            )
        _, stderr = process.communicate()  # Capture uniquement stderr
        
        if process.returncode != 0 and stderr.strip():
            # On n'affiche que les erreurs significatives
            error_msg = stderr.strip().split('\n')[-1]  # Dernière ligne d'erreur
            self.log_message(f"{log_prefix}ERREUR: {error_msg}")

            #"-c:v", "libx264", "-preset", "medium", "-crf", "23",
            #"-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",

        return process.returncode
        


    def cut_and_save_clips(self, video_path, timestamps, interval=0):
        # Création d'une queue pour les messages inter-threads
        self.message_queue = queue.Queue()
        self.stop_processing = False
        
        # Démarrer le thread qui traite les messages
        self.window.after(100, self.process_messages)
        
        # Démarrer le traitement dans un thread séparé
        threading.Thread(target=self._process_clips, 
                    args=(video_path, timestamps, interval),
                    daemon=True).start()

    def _process_clips(self, video_path, timestamps, interval):
        """Fonction exécutée dans le thread de traitement"""
        try:
            # Vérification de la durée
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ], capture_output=True, text=True)

            try:
                duration = float(result.stdout.strip())
            except:
                self.message_queue.put(("[ERROR] Unable to read video duration.", "error"))
                return

            # Génération des timestamps si intervalle spécifié
            if interval > 0:
                time = interval
                while duration > time:
                    timestamps.append(time)
                    time += interval

            # Construction de la liste complète [0, cuts..., end]
            if not timestamps:
                timestamps = [0.0, duration]
            else:
                timestamps = [0.0] + timestamps + [duration]

            self.message_queue.put((f"[INFO] Segments : {timestamps}", "info"))

            # Préparation du dossier de sortie
            base_dir = "C:\\PYGAME\\clips"
            output_dir = os.path.join(base_dir, os.path.basename(video_path)[:-4])
            os.makedirs(output_dir, exist_ok=True)

            EPSILON = 0.001  # 1 ms

            # Utilisation d'un pool de threads pour traiter plusieurs clips en parallèle
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as executor:
                futures = []
                for i in range(len(timestamps) - 1):
                    if self.stop_processing:
                        break
                        
                    start = timestamps[i]
                    end = timestamps[i + 1]
                    length = end - start

                    if i < len(timestamps) - 2:
                        length -= EPSILON
                    
                    output_file = os.path.join(output_dir, f"clip_{i:03}.mp4")
                    
                    futures.append(
                        executor.submit(
                            self._process_single_clip,
                            video_path, start, length, output_file, i
                        )
                    )

                # Attendre la fin de tous les clips
                for future in futures:
                    if self.stop_processing:
                        future.cancel()
                    else:
                        future.result()
            self.message_queue.put((f"[OK] End process", "success"))

        except Exception as e:
            self.message_queue.put((f"[ERREUR GLOBALE] {str(e)}", "error"))

    def _process_single_clip(self, video_path, start, length, output_file, clip_num):
        """Traitement d'un seul clip"""
        if self.stop_processing:
            return False

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", str(start), "-t", str(length),
            "-vf", "scale=w=608:h=1080:force_original_aspect_ratio=increase,crop=608:1080",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-c:a", "aac", output_file
        ]
        
        self.message_queue.put((f"Début du traitement du clip {clip_num}", "info"))
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
                encoding='utf-8'
            )
            
            # for line in process.stdout:
            #     if self.stop_processing:
            #         process.terminate()
            #         break
            #     self.message_queue.put(f"Clip {clip_num}: {line.strip()}", "debug")
            
            return_code = process.wait()
            
            if return_code == 0:
                self.message_queue.put((f"[SUCCÈS] Clip {clip_num} créé ({length:.2f}s)", "info"))
                if self.extract_audio_var.get():
                    self.extract_audio(video_path, start, length, os.path.dirname(output_file), clip_num)
                return True
            else:
                self.message_queue.put((f"[ÉCHEC] Clip {clip_num} non créé", "error"))
                return False
                
        except Exception as e:
            self.message_queue.put((f"[ERREUR] Clip {clip_num}: {str(e)}", "error"))
            return False

    def process_messages(self):
        """Traite les messages dans la queue (à appeler périodiquement)"""
        try:
            while True:
                #message, level = self.message_queue.get_nowait()
                # Gestion rétrocompatible (item peut être str ou tuple)
                item = self.message_queue.get_nowait()
                if isinstance(item, tuple):
                    message, level = item
                else:
                    message = item
                    level = "info"  # Valeur par défaut
        
                # On ignore complètement les messages de debug
                if level == "debug":
                    continue

                # Ajout avec couleur selon le niveau
                if level == "error":
                    self.log_text.tag_config("error", foreground="red")
                    self.log_text.insert("end", message + "\n", "error")
                elif level == "success":
                    self.log_text.tag_config("success", foreground="green")
                    self.log_text.insert("end", message + "\n", "success")
                else:
                    self.log_text.insert("end", message + "\n")
                    
                self.log_text.see("end")
                self.window.update_idletasks()
                
        except queue.Empty:
            pass
        
        self.window.after(100, self.process_messages)

    def cancel_processing(self):
        """Permet d'annuler le traitement en cours"""
        self.stop_processing = True
        self.message_queue.put(("[INFO] Traitement annulé par l'utilisateur", "info"))