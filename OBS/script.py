import obspython as obs

try:
    import win32gui, win32process, psutil
except ImportError:
    obs.script_log(obs.LOG_ERROR, "⚠️ Le module win32gui est requis (pywin32). Installe-le via pip.")
    raise

def find_window_info():
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "pygame" in title.lower():
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    print(f"🪟 '{title}' - process: {proc.name()}")
                except Exception:
                    pass
    win32gui.EnumWindows(callback, None)



# === CONFIGURATION ===
window_title = "pygame window"
source_name = "CapturePygame"
recording = False

def script_description():
    return "Capture automatiquement une fenêtre nommée 'pygame window' et enregistre tant qu'elle est visible."

def script_load(settings):
    print("🎬 Capture automatique de la fenêtre 'pygame window'...")
    find_window_info()
    obs.timer_add(check_and_capture, 1000)

def script_unload():
    obs.timer_remove(check_and_capture)

def check_and_capture():
    global recording
    hwnd = win32gui.FindWindow(None, window_title)

    if hwnd != 0 and win32gui.IsWindowVisible(hwnd):
        if not recording:
            # Créer ou activer la source
            create_window_capture_source()
            obs.script_log(obs.LOG_INFO, f"🎬 '{window_title}' détectée, enregistrement...")
            obs.obs_frontend_recording_start()
            recording = True
    else:
        if recording:
            obs.script_log(obs.LOG_INFO, f"⏹ '{window_title}' fermée, arrêt.")
            obs.obs_frontend_recording_stop()
            recording = False
            remove_capture_source()

def create_window_capture_source():
    scene = obs.obs_frontend_get_current_scene()
    scene_source = obs.obs_scene_from_source(scene)

    existing = obs.obs_get_source_by_name(source_name)
    if existing is None:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "window", f"{window_title}:pygame.exe")  # ← Remplace pygame.exe si nécessaire
        obs.obs_data_set_bool(settings, "capture_cursor", True)

        source = obs.obs_source_create("window_capture", source_name, settings, None)
        scene_item = obs.obs_scene_add(scene_source, source)

        obs.obs_data_release(settings)
        obs.obs_source_release(source)
    else:
        obs.obs_source_release(existing)
    obs.obs_source_release(scene)

def remove_capture_source():
    scene = obs.obs_frontend_get_current_scene()
    scene_source = obs.obs_scene_from_source(scene)

    item = obs.obs_scene_find_source(scene_source, source_name)
    if item:
        obs.obs_sceneitem_remove(item)
    obs.obs_source_release(scene)
