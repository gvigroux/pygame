import os
import re
import shutil
import subprocess
import cv2
import ttkbootstrap as ttk
import vlc
from ui.log import log_message
from PIL import Image, ImageTk


current_player = None
current_video_frame = None

def play_video_vlc(state, video_path, parent):
    global current_player, current_video_frame

    log_message(state, f"Play video [{video_path}]")
    # Si une vidéo est déjà lancée, stop et détruit la zone vidéo
    if current_player is not None:
        current_player.stop()
        current_player.release()
        current_player = None
    if current_video_frame is not None:
        current_video_frame.destroy()
        current_video_frame = None

    # Crée un nouveau frame pour la vidéo
    current_video_frame = ttk.Frame(parent, width=304, height=540)
    current_video_frame.pack()

    instance = vlc.Instance()
    player = instance.media_player_new()

    handle = current_video_frame.winfo_id()

    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_hwnd(handle)  # Windows

    player.play()

    current_player = player



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

    if not timestamps:
         # Copier la vidéo originale en tant que clip_0.mp4
        clip_path = os.path.join(output_dir, "clip_0.mp4")
        try:
            shutil.copy2(input_path, clip_path)
            log_message(state, f"No scene change detected, copied original video as clip_0.mp4")
        except Exception as e:
            log_message(state, f"[ERROR] Unable to copy original video as clip_0.mp4: {str(e)}")
        return

    log_message(state, f"[{len(timestamps)+1}] cuts detected.")

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

    timestamps = [0.0] + timestamps + [duration]

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








# def play_video(path):
#     # Méthode 1 : ouvrir avec le lecteur vidéo par défaut (Windows/Mac/Linux)
#     if os.name == 'nt':  # Windows
#         os.startfile(path)
#     elif os.name == 'posix':  # macOS / Linux
#         subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', path))


# video_window = None
# video_cap = None
# video_label = None

# def play_video_in_window(video_path):
#     global video_window, video_cap, video_label

#     if video_window and video_window.winfo_exists():
#         video_window.destroy()

#     video_window = ttk.Toplevel()  # Utilise ttkbootstrap
#     video_window.title(f"Lecture : {os.path.basename(video_path)}")

#     video_label = ttk.Label(video_window)
#     video_label.pack(padx=10, pady=10)

#     video_cap = cv2.VideoCapture(video_path)

#     def update_frame():
#         if video_cap.isOpened():
#             ret, frame = video_cap.read()
#             if ret:
#                 frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 img = Image.fromarray(frame)
#                 imgtk = ImageTk.PhotoImage(image=img)
#                 video_label.imgtk = imgtk  # garder une référence
#                 video_label.configure(image=imgtk)
#                 video_window.after(30, update_frame)
#             else:
#                 video_cap.release()
#                 video_window.destroy()

#     update_frame()

# video_cap = None
# playing = False

# def play_video_inline(video_path):
#     global video_cap, playing

#     if video_cap is not None:
#         video_cap.release()

#     video_cap = cv2.VideoCapture(video_path)
#     playing = True

#     def update_frame():
#         if not playing:
#             return
#         ret, frame = video_cap.read()
#         if ret:
#             #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             #img = Image.fromarray(frame)

#             # Calcul ratio et taille cible
#             target_width = 320
#             orig_height, orig_width = frame.shape[:2]
#             ratio = target_width / orig_width
#             new_height = int(orig_height * ratio)
#             frame_resized = cv2.resize(frame, (target_width, new_height), interpolation=cv2.INTER_AREA)
#             img = Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB))


#             imgtk = ImageTk.PhotoImage(image=img)
#             video_label.imgtk = imgtk
#             video_label.config(image=imgtk)
#             video_label.after(30, update_frame)
#         else:
#             video_cap.release()

#     update_frame()