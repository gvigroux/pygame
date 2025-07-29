import json
import re
import threading
import time
from tkinter import filedialog
import unicodedata

from object.video import Video
from object.object_factory import ObjectFactory




def load_videos_sequentially(videos):
    """
    Charge chaque vidéo une par une.
    La fonction attend que le chargement de chaque vidéo soit terminé avant de passer à la suivante.
    """
    for video in videos:
        #print(f"[LOAD] Début du chargement de: {video.label}")
        video.load()
        
        # Boucle d'attente pendant le chargement
        while not video.is_ready():
            time.sleep(0.1)  # petit sleep pour ne pas bloquer complètement
        

######################################


# def load_scene_dialog(state):
#     filepath = filedialog.askopenfilename(
#         title="Open scene",
#         defaultextension=".json",
#         filetypes=[("JSON files", "*.json")])
#     if filepath:
#         state["config"].setdefault("current", {})["file_path"] = filepath
#         load_scene(state)


def load_scene(state):

    # Check current file path
    current = state["config"].get("current", {})
    filepath = current.get("file_path", "")

    if len(filepath) <= 0:
        return
    
    # Reset objects
    state["game"].reset()
    state["library"].reset()
    state["timeline"].reset()
    

    state["game"].load(filepath, True, False)


    track_count = 0
    for data in state["game"].config.get("objects", []):
        object = state["library"].get_video(data.get("path"))
        if object is None:
            # When Video not in path or any other object (beacause no path as well)
            object = ObjectFactory.create(data, state["game"].window_size, 0, 0)
            track_count = max(object.track_id,track_count)
            state["library"].add_clip(object)
        else:
            object = object.clone()
            object.step.delay = data.get("step", {}).get("delay", 0)
        state["game"].objects.append(object)

    # Legacy import rule
    if( track_count == 0) :
        i = len(state["game"].objects)-1
        for object in state["game"].objects:
            state["timeline"].add_track_top(False)
            state["timeline"].add_clip(object, track=i, start=object.step.delay, duration=object.step.duration)
            i-=1
    else:
        for i in range(track_count+1):
            state["timeline"].add_track_top(False)
        for object in state["game"].objects:
            state["timeline"].add_clip(object, track=object.track_id, start=object.step.delay, duration=object.step.duration)

    
    for object in state["game"].objects:
        if( isinstance(object, Video) ):
            # TODO: je charge les metadatas plusieurs fois si c'est le meme path
            object.load_metadata_async()

    state["game"].start_lazy_loading()
    #threading.Thread(target=load_videos_sequentially, args=(videos,), daemon=True).start()
  


######################################


def save_scene(state):
    
    current     = state["config"].get("current", {})
    file_path   = current.get("file_path", "")

    # Vérifie que c’est bien une chaîne non vide
    if not isinstance(file_path, str) or not file_path.strip():
        return

    # 1️⃣ Charger le JSON existant
    data = {}

    state["game"].reorder_objects()

    data["objects"] = []
    for object in state["game"].objects:
        obj = object.serialize_object()
        obj["track_id"] = object.track_id
        data["objects"].append(obj) 

    data.setdefault("settings", {}).update(state["game"].get_settings())
        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


######################################



def clean_filename(name, max_length=255):
    # Normaliser les accents (é -> e, etc.)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()

    # Remplacer les caractères interdits par un underscore
    # Caractères interdits courants : \ / : * ? " < > | et aussi control chars
    name = re.sub(r'[\\/:*?"<>|]', '_', name)

    # Supprimer les caractères non imprimables ou spéciaux
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)

    # Remplacer les espaces multiples par un seul underscore
    name = re.sub(r'\s+', '_', name)

    # Tronquer si trop long
    if len(name) > max_length:
        name = name[:max_length]

    # Supprimer les points au début ou fin (pas permis sur certains OS)
    name = name.strip('.')

    # Optionnel : forcer minuscule
    # name = name.lower()

    return name
