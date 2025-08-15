import json
import re
import threading
import time
from tkinter import filedialog
import unicodedata

from object.video import Video
from object.object_factory import ObjectFactory




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
        for i in range(4):
            state["timeline"].add_track_top(False)
        return
    
    # Reset objects
    state["game"].reset()
    state["library"].reset()
    state["timeline"].reset()
    

    state["game"].load(filepath, True, False)

    track_count = 2
    use_library = False
    for data in state["game"].config.get("library", []):
        object = ObjectFactory.create(data, state["game"].window_size, 0, 0)
        track_count = max(object.track_id,track_count)
        state["library"].add_clip(object)
        use_library = True


    for data in state["game"].config.get("objects", []):
        object = state["library"].get_clip_by_uid(data.get("uid"))
        
        if object is None:
            # The Clip is not in Libray, we need to add it
            object = ObjectFactory.create(data, state["game"].window_size, 0, 0)
            track_count = max(object.track_id,track_count)
            state["library"].add_clip(object)
        else:
            # TODO: It's not really logical, I should clone and just copy position, step and trackId
            object = ObjectFactory.create(data, state["game"].window_size, 0, 0)
            track_count = max(object.track_id,track_count)
            #object = object.clone()
            #object.step.delay = data.get("step", {}).get("delay", 0)
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

    
    # TODO: je charge les metadatas plusieurs fois (au moins 2)
    for object in state["library"]._all_clips:
        if( isinstance(object, Video) ):
            object.load_metadata_async()

    for object in state["game"].objects:
        if( isinstance(object, Video) ):
            object.load_metadata_async()

    # Reoder objects to be sure to start loading the first videos
    state["game"].reorder_objects()
    uid_order = {
        obj.uid: index
        for index, obj in enumerate(
            sorted(state["game"].objects, key=lambda obj: obj.step.delay)
        )
    }
    state["library"]._all_clips.sort(key=lambda obj: uid_order.get(obj.uid, float("inf")))
    state["library"].start_lazy_loading()
    # state["game"].start_lazy_loading()


######################################


def save_scene(state):
    
    current     = state["config"].get("current", {})
    file_path   = current.get("file_path", "")

    # Vérifie que c’est bien une chaîne non vide
    if not isinstance(file_path, str) or not file_path.strip():
        return False

    # 1️⃣ Charger le JSON existant
    data = {}

    state["game"].reorder_objects()

    data["objects"] = []
    for object in state["game"].objects:
        obj = object.serialize_object()
        obj["track_id"] = object.track_id
        data["objects"].append(obj)

    data["library"] = []
    for object in state["library"]._all_clips:
        obj = object.serialize_object()
        data["library"].append(obj)    

    data.setdefault("settings", {}).update(state["game"].get_settings())
        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return True

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
