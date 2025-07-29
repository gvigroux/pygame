
import json
import os

from ui.file import load_scene


CONFIG_FILE = "ui.json"


def save_config(state):

    # 1️⃣ Charger le JSON existant
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["config"] = state["config"]

    is_maximized = state["app"].state() == "zoomed"
    layout = {
        "pane_sizes": [state["horizontal_paned"].sashpos(0), state["horizontal_paned"].sashpos(1)],
        "vertical_sash": state["vertical_paned"].sashpos(0),
        "window_size": (state["app"].winfo_width(), state["app"].winfo_height()),
        "maximized": is_maximized
    }
    data["layout"] = layout

        
    # 3️⃣ Réécrire le fichier avec la nouvelle config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        
  

def load_config(state):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            state["config"] = data["config"]

            layout = data["layout"]

            if layout.get("maximized"):
                state["app"].state("zoomed")
            
            if "pane_sizes" in layout:
                def apply_pane_sizes():
                    state["app"].update_idletasks()
                    # ✅ Forcer une taille minimale
                    total_width = state["horizontal_paned"].winfo_width()
                    if total_width < 50:  # trop petit, pas encore affiché
                        state["app"].after(100, apply_pane_sizes)
                        return
                    try:
                        state["horizontal_paned"].sashpos(0, layout["pane_sizes"][0])
                        state["horizontal_paned"].sashpos(1, layout["pane_sizes"][1])
                    except Exception as e:
                        print("Erreur lors de la restauration du layout :", e)
                state["app"].after(200, apply_pane_sizes)

            if "window_size" in layout:            
                state["app"].geometry(f"{layout['window_size'][0]}x{layout['window_size'][1]}")

            if "vertical_sash" in layout:
                def apply_vertical_pane_sizes():
                    state["app"].update_idletasks()
                    # ✅ Forcer une taille minimale
                    total_height = state["vertical_paned"].winfo_height()
                    if total_height < 50:  # trop petit, pas encore affiché
                        state["app"].after(100, apply_vertical_pane_sizes)
                        return
                    try:
                        state["vertical_paned"].sashpos(0, layout["vertical_sash"])
                    except Exception as e:
                        print("Erreur vertical sash :", e)
                state["app"].after(200, apply_vertical_pane_sizes)

            load_scene(state)
                  
