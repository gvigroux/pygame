import pygame
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os
import tkinter as tk

from game import Game
from object.object import Object
from ui.helper import center_window
from ui.tools.downloader import DownloaderWindow
from ui.tools.library import LibraryWindow
from ui.tools.timeline import Timeline
from ui.tools.toolbar import Toolbar
from ui.tools.type_chooser import TypeChooser


state = {
    'log': None,
    "config": {
        "downloader": {
            "url": "",
            "split": "",
        }
    }
}


######################################


def save_scene(state, scene_filepath, game):

    # 1️⃣ Charger le JSON existant
    with open(scene_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["objects"] = []
    for object in game.objects:
        data["objects"].append(object.data) 
        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(scene_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        







CONFIG_FILE = "ui.json"


def save_config(state):

    # 1️⃣ Charger le JSON existant
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["config"] = state["config"]
        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        
  

def load_config(state):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            state["config"] = json.load(f)

######################################

load_config(state)

######################################
pygame.init()
game = Game(pygame)
game.load(avoid_debug=False)
######################################



# Conteneur unique global pour toutes les propriétés
if 'properties_container' not in globals():
    properties_container = None

def show_object_properties(obj, parent=None):
    global properties_container

    # Créé 1 seule fois le conteneur principal
    if properties_container is None:
        properties_container = ttk.Frame(parent)
        properties_container.pack(fill="both", expand=True)

    # Nettoyage : détruit seulement l'intérieur
    for widget in properties_container.winfo_children():
        widget.destroy()

    # Remplit la racine
    show_object_properties_fixed("main", obj.data, obj, properties_container, show_children=False)

    for key, value in obj.schema().items():
        if value[0] not in ("str", "float", "int", "bool"):
            show_object_properties_fixed(
                key,
                obj.data.get(key, {}),
                getattr(obj, key, {}),
                properties_container
            )


def show_object_properties_fixed(name, data, obj, parent=None, show_children=True):
    if parent is None:
        raise ValueError("Parent requis")

    parent.columnconfigure(0, weight=1)

    spec = obj.schema()
    if not spec:
        ttk.Label(parent, text=f"No spec for {name}").pack()
        return

    section = ttk.Frame(parent, borderwidth=1, relief="solid")
    section.grid(sticky="ew", padx=5, pady=5)
    section.columnconfigure(0, weight=1)

    # Header style
    frame_style = "Titlebar.Enabled.TFrame" if obj.enabled() else "Titlebar.Disabled.TFrame"
    label_style = "Titlebar.Enabled.TLabel" if obj.enabled() else "Titlebar.Disabled.TLabel"

    header = ttk.Frame(section, style=frame_style)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(1, weight=1)

    arrow_label = ttk.Label(header, text="►", style=label_style)
    arrow_label.grid(row=0, column=0, sticky="w", padx=(5, 5))

    title_label = ttk.Label(header, text=name.upper(), style=label_style)
    title_label.grid(row=0, column=1, sticky="w", padx=(0, 5))

    # Contenu différé (lazy)
    content = None
        
    def build_content():
        nonlocal content
        content = ttk.Frame(section, padding=10)
        content.grid(row=1, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)
        content.columnconfigure(0, weight=0, minsize=70)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=1)

        row_counter = 0

        # ✅ Liste pour garder toutes les variables liées aux champs
        all_vars = []

        for i, (key, (field_type, field_label)) in enumerate(spec.items()):
            raw_value = data.get(key, "")
            calculated_value = getattr(obj, key, "")

            if field_type in ("int", "float", "str"):
                lbl = ttk.Label(content, text=f"{field_label}:")
                lbl.grid(row=row_counter, column=0, sticky="e", padx=5, pady=2)

                var = tk.StringVar(value=str(raw_value))
                entry = ttk.Entry(content, textvariable=var)
                entry.grid(row=row_counter, column=1, sticky="ew", padx=(0, 2), pady=2)

                result_var = tk.StringVar(value=str(calculated_value))
                entry2 = ttk.Entry(content, textvariable=result_var, state="readonly")
                entry2.grid(row=row_counter, column=2, sticky="ew", padx=(2, 0), pady=2)

                # ✅ On mémorise ce couple pour MAJ globale après un prepare()
                all_vars.append((key, var, result_var))

                def recalculate(*args, key=key, var=var):
                    try:
                        val = var.get()
                        setattr(obj, key, val)
                        if hasattr(data, "set"):
                            data.set(key, val)
                        else:
                            data[key] = val

                        obj.prepare()

                        # ✅ Après prepare, relire TOUT et MAJ TOUT
                        for k, v, res_v in all_vars:
                            v.set(str(data.get(k, "")))
                            res_v.set(str(getattr(obj, k, "")))

                    except Exception as e:
                        print(e)

                var.trace_add("write", recalculate)

                row_counter += 1

            elif field_type == "bool":
                lbl = ttk.Label(content, text=f"{field_label}:")
                lbl.grid(row=row_counter, column=0, sticky="e", padx=5, pady=2)
                var = tk.BooleanVar(value=bool(raw_value))
                check = ttk.Checkbutton(content, variable=var)
                check.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)
                row_counter += 1

            else:
                if not show_children:
                    continue
                subframe = ttk.Frame(content)
                subframe.grid(row=row_counter + 1, column=0, columnspan=3, sticky="ew", padx=(20, 0))
                sub_object = getattr(obj, key, "")
                show_object_properties_fixed(key, data.get(key, {}), sub_object, subframe)
                row_counter += 2

    def toggle():
        nonlocal content
        if content is None:
            build_content()
            arrow_label.config(text="▼")
        elif content.winfo_ismapped():
            content.grid_remove()
            arrow_label.config(text="►")
        else:
            content.grid()
            arrow_label.config(text="▼")

    header.bind("<Button-1>", lambda e: toggle())
    for child in header.winfo_children():
        child.bind("<Button-1>", lambda e: toggle())






# def show_object_properties(object, parent=None):
#     # Nettoyage toujours
#     for widget in parent.winfo_children():
#         widget.destroy()

        
#     show_object_properties_fixed("main", object.data, object, parent, False)

#     for i, (key, value) in enumerate(object.schema().items()):
#         if( value[0] not in ("str", "float", "int", "bool") ):
#             show_object_properties_fixed(key,        object.data.get(key, {}), getattr(object, key, {}), parent)

    

# def show_object_properties_fixed(name, data, object, parent=None, show_children=True):
#     if parent is None:
#         parent = zone3_content

#     parent.columnconfigure(0, weight=1)

#     spec = object.schema()
#     if not spec:
#         ttk.Label(parent, text=f"No spec for {name}").pack()
#         return

#     section = ttk.Frame(parent, borderwidth=1, relief="solid")
#     section.grid(sticky="ew", padx=5, pady=5)
#     section.columnconfigure(0, weight=1)

#     # === Header ===
    
#     # Choisir le style dynamiquement
#     if object.enabled():
#         frame_style = "Titlebar.Enabled.TFrame"
#         label_style = "Titlebar.Enabled.TLabel"
#     else:
#         frame_style = "Titlebar.Disabled.TFrame"
#         label_style = "Titlebar.Disabled.TLabel"

#     header = ttk.Frame(section, style=frame_style)
#     header.grid(row=0, column=0, sticky="ew")
#     header.columnconfigure(1, weight=1)

#     arrow_label = ttk.Label(header, text="▼", style=label_style)
#     arrow_label.grid(row=0, column=0, sticky="w", padx=(5, 5))

#     title_label = ttk.Label(header, text=name.upper(), style=label_style)
#     title_label.grid(row=0, column=1, sticky="w", padx=(0, 5))



#     content = ttk.Frame(section, padding=10)
#     content.grid(row=1, column=0, sticky="ew")

#     # Bien configurer pour que tout s’étale
#     parent.columnconfigure(0, weight=1)
#     section.columnconfigure(0, weight=1)
#     content.columnconfigure(0, weight=0, minsize=70)  
#     content.columnconfigure(1, weight=1)
#     content.columnconfigure(2, weight=1)

#     row_counter = 0
#     for i, (key, (field_type, field_label)) in enumerate(spec.items()):
#         raw_value = data.get(key, "")
#         calculated_value = getattr(object, key, "")


#         if field_type in ("int", "float", "str"):
#             lbl = ttk.Label(content, text=f"{field_label}:")
#             lbl.grid(row=row_counter, column=0, sticky="e", padx=5, pady=2)

#             entry = ttk.Entry(content)
#             entry.insert(0, str(raw_value))
#             entry.grid(row=row_counter, column=1, sticky="ew", padx=(0, 2), pady=2)
            
#             entry2 = ttk.Entry(content) 
#             entry2.insert(0, str(calculated_value))
#             entry2.grid(row=row_counter, column=2, sticky="ew", padx=(2, 0), pady=2)
#             row_counter += 1

#         elif field_type == "bool":
#             lbl = ttk.Label(content, text=f"{field_label}:")
#             lbl.grid(row=row_counter, column=0, sticky="e", padx=5, pady=2)
#             var = tk.BooleanVar(value=bool(raw_value))
#             check = ttk.Checkbutton(content, variable=var)
#             check.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)
#             row_counter += 1

#         else:
#             if( not show_children ):
#                 continue

#             # Sous-frame dédiée pour éviter de polluer la grille du parent
#             subframe = ttk.Frame(content)
#             subframe.grid(row=row_counter+1, column=0, columnspan=3, sticky="ew", padx=(20, 0))

#             sub_object = getattr(object, key, "")
#             show_object_properties_fixed(key, data.get(key, {}), sub_object, subframe)
            
#             row_counter += 2

#     # === Toggle ===
#     def toggle():
#         if content.winfo_ismapped():
#             content.grid_remove()
#             arrow_label.config(text="►")
#         else:
#             content.grid()
#             arrow_label.config(text="▼")

    
#     if( show_children ):
#         content.grid_remove()
#         arrow_label.config(text="►")

#     header.bind("<Button-1>", lambda e: toggle())
#     for child in header.winfo_children():
#         child.bind("<Button-1>", lambda e: toggle())





#################################################

app = ttk.Window(themename="superhero")
app.title("TikTok Maker")
center_window(app, 1080, 720)
app.resizable(True, True)


state['app'] = app

 # Frame principale qui contient tout
main_frame = ttk.Frame(app)
main_frame.pack(fill="both", expand=True)

# Définir une grille à 3 lignes :
main_frame.rowconfigure(0, weight=0)  # Toolbar / séparateur
main_frame.rowconfigure(1, weight=1)  # Le centre : frame_game + timeline
main_frame.rowconfigure(2, weight=0)  # Log en bas
main_frame.columnconfigure(0, weight=1)


#################################################

toolbar = Toolbar(main_frame)
toolbar.add_icon("ui/icons/icons8-download-from-the-cloud-24.png", lambda: DownloaderWindow(state))
toolbar.add_icon("ui/icons/icons8-video-gallery-24.png", lambda: LibraryWindow(state))
toolbar.add_icon("ui/icons/icons8-upload-to-the-cloud-24.png", lambda: save_scene(state, "config.json", game))

# Séparateur en dessous
separator = ttk.Separator(main_frame, orient="horizontal")
separator.grid(row=0, column=0, sticky="ew", pady=(40,0))  # Ajuste le `pady` si besoin

#################################################

center_frame = ttk.Frame(main_frame)
center_frame.grid(row=1, column=0, sticky="nsew")
center_frame.rowconfigure(0, weight=1)  # Frame_game
center_frame.rowconfigure(1, weight=0)  # timeline_toolbar
center_frame.rowconfigure(2, weight=0)  # Timeline
center_frame.columnconfigure(0, weight=1)



# === Ton frame_game ===
frame_game = ttk.Frame(center_frame)
frame_game.grid(row=0, column=0, sticky="nsew")

# Configurer les lignes (note le weight)
frame_game.rowconfigure(0, weight=0)  # Toolbar en haut, hauteur fixe
frame_game.rowconfigure(1, weight=1)  # Zone1, 2, 3 prennent le reste

# Configurer les colonnes (3 égales)
for col in range(3):
    frame_game.columnconfigure(col, weight=1)


# Créer les 3 zones verticales
zone1 = ttk.Frame(frame_game, padding=10, borderwidth=1, relief="solid")
zone1.grid(row=1, column=0, sticky="nsew")


zone2 = ttk.Frame(frame_game, padding=10, borderwidth=1, relief="solid")
zone2.grid(row=1, column=1, sticky="nsew")


# === Zone3 scrollable ===

# Frame qui contiendra le canvas + scrollbar
zone3_container = ttk.Frame(frame_game, padding=0, borderwidth=0)
zone3_container.grid(row=1, column=2, sticky="nsew")

# Le canvas qui contiendra le contenu scrollable
zone3_canvas = ttk.Canvas(zone3_container)
zone3_scrollbar = ttk.Scrollbar(zone3_container, orient="vertical", command=zone3_canvas.yview)
zone3_canvas.configure(yscrollcommand=zone3_scrollbar.set)

zone3_scrollbar.pack(side="right", fill="y")
zone3_canvas.pack(side="left", fill="both", expand=True)

# Frame interne qui sera scrollée
zone3_content = ttk.Frame(zone3_canvas)
zone3_content.columnconfigure(0, weight=1)
zone3_window = zone3_canvas.create_window((0, 0), window=zone3_content, anchor="nw")



def _resize_zone3_content(event):
    canvas_width = event.width
    zone3_canvas.itemconfig(zone3_window, width=canvas_width)

zone3_canvas.bind("<Configure>", _resize_zone3_content)

# Ajuster le scrollregion quand le contenu change
def _on_zone3_configure(event):
    zone3_canvas.configure(scrollregion=zone3_canvas.bbox("all"))

zone3_content.bind("<Configure>", _on_zone3_configure)

def _on_mousewheel(event):
    # Vérifie où est la souris
    widget = event.widget
    if widget == zone3_canvas or widget.winfo_toplevel().focus_displayof() == zone3_canvas:
        zone3_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    elif str(widget).startswith(str(zone3_content)):
        zone3_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

zone3_canvas.bind_all("<MouseWheel>", _on_mousewheel)
zone3_canvas.bind_all("<Button-4>", lambda e: zone3_canvas.yview_scroll(-1, "units"))
zone3_canvas.bind_all("<Button-5>", lambda e: zone3_canvas.yview_scroll(1, "units"))


frame_game.grid_columnconfigure(0, minsize=300)
frame_game.grid_columnconfigure(1, minsize=300)
frame_game.grid_columnconfigure(2, minsize=300)


############################################

# Toolbar de la timeline
timeline_toolbar = ttk.Frame(center_frame)
timeline_toolbar.grid(row=1, column=0, sticky="ew")


############################################

def show_clip_properties(object):
    print("Clip sélectionné :", object)        
    show_object_properties(object, zone3_content)


num_tracks = len(game.objects)
timeline = Timeline(center_frame, num_tracks=num_tracks, length=120, on_clip_click=show_clip_properties)
timeline.grid(row=2, column=0, sticky="ew")


i = num_tracks-1
for object in game.objects:
    timeline.add_clip( object, track=i, start=object.step.delay, duration=object.step.duration)
    i-=1
    pass

############################################
def get_subclasses(cls):
    subclasses = set()
    work = [cls]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses


def open_type_chooser():
    def handle_choice(choice):
        print("Vous avez choisi :", choice)
        
        track_index = timeline.add_track_top()
        data = json.loads('''
        {{
            "type": "{choice}",
            "label": "New {choice}", 
            "step" : {{"duration": 2}}
        }}
        '''.format(choice=choice))
        object = game.add_object(data)
        timeline.add_clip(object, track=track_index, start=object.step.delay, duration=object.step.duration)

    subclasses = get_subclasses(Object)
    type_list = sorted([cls.__name__ for cls in subclasses])
    TypeChooser(app, type_list, handle_choice)



# Exemple de bouton :
ttk.Button(timeline_toolbar, text="Ajouter clip", command=open_type_chooser).pack(side="left")
ttk.Button(timeline_toolbar, text="Supprimer clip").pack(side="left")
ttk.Button(timeline_toolbar, text="Zoom +").pack(side="left")
ttk.Button(timeline_toolbar, text="Zoom -").pack(side="left")


############################################

# Bas : zone de log partagée
log_frame = ttk.Frame(main_frame)
log_frame.grid(row=2, column=0, sticky="ew")
state['log'] = ttk.Text(log_frame, height=8, state='disabled', wrap='word')
state['log'].pack(fill='both', expand=True, padx=5, pady=0)




# Sauvegarder à la fermeture
app.protocol("WM_DELETE_WINDOW", lambda: (save_config(state), app.destroy()))


style = ttk.Style()
style.configure("Selected.TFrame", background="lightblue")
style.configure("Selected.TLabel", background="lightblue", foreground="black")

style.configure("Titlebar.TFrame", background="#0a283b")
style.configure("Titlebar.TLabel", background="#0a283b", foreground="white", font=("Rototo", 10, "bold"))
#style.configure("Titlebar.TFrame", background=style.colors.primary)

# Style pour bloc activé
style.configure("Titlebar.Enabled.TFrame", background="#0a283b")
style.configure("Titlebar.Enabled.TLabel", background="#0a283b", foreground="white")

# Style pour bloc désactivé
style.configure("Titlebar.Disabled.TFrame", background="#A55C21")
style.configure("Titlebar.Disabled.TLabel", background="#A55C21", foreground="#dddddd")



# Lancer l'app
app.mainloop()





#https://www.tiktok.com/@funny_cute_pets_lover/video/7453151818730818849?q=compliation%20chaton&t=1751804300007 
