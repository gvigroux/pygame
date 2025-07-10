import os
from tkinter import messagebox, filedialog
import yt_dlp

from ui.file import clean_filename
from ui.log import log_message


def download_video(state, url_entry, split_entry):
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Erreur", "Veuillez entrer une URL.")
        return
    
    log_message(state, f"Downloading: {url}...")

    #output_dir = filedialog.askdirectory(title="Choisir le dossier de téléchargement")
    #if not output_dir:
    #    return
    output_dir = "C:\\PYGAME\\tmp"

    ydl_opts = {
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'format': 'best',
        'nocheckcertificate': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'requested_downloads' in info and info['requested_downloads']:
                path = info['requested_downloads'][0]['filepath']
                megabytes = info['requested_downloads'][0]['filesize'] / (1024 * 1024)
                log_message(state, f"Download complete ({info['duration_string']}/{megabytes:.2f} MB)!")
            else:
                # Fallback si la clé 'requested_downloads' n’est pas disponible
                path = ydl.prepare_filename(info)
                log_message(state, f"Download complete!")

            # Nettoyage du nom de fichier
            base_dir = os.path.dirname(path)
            filename = os.path.basename(path)
            clean_name = clean_filename(filename)

            new_path = os.path.join(base_dir, clean_name)
            if new_path != path:
                os.rename(path, new_path)
                log_message(state, f"File renamed to: {clean_name}")
                path = new_path
            
            split_entry.delete(0, 'end')
            split_entry.insert(0, path) 
    except Exception as e:
        log_message(state, f"[ERROR] An error occurred: {str(e)}")