import obspython as obs
import win32gui

window_title = "pygame window"
recording = False

def script_description():
    return "Démarre/arrête l'enregistrement selon la présence de la fenêtre 'pygame window'."

def script_load(settings):
    obs.timer_add(check_window, 1000)

def script_unload():
    obs.timer_remove(check_window)

def check_window():
    global recording
    hwnd = win32gui.FindWindow(None, window_title)

    if hwnd != 0 and win32gui.IsWindowVisible(hwnd):
        if not recording:
            obs.script_log(obs.LOG_INFO, "🎬 Fenêtre détectée, démarrage de l'enregistrement")
            obs.obs_frontend_recording_start()
            recording = True
    else:
        if recording:
            obs.script_log(obs.LOG_INFO, "⏹ Fenêtre fermée, arrêt de l'enregistrement")
            obs.obs_frontend_recording_stop()
            recording = False
