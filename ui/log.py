from ttkbootstrap.constants import *


def log_message(state, message):
    log_text = state['log']
    log_text.config(state='normal')          # Rendre modifiable
    log_text.insert(END, message + "\n")     # Ajouter texte à la fin
    log_text.see(END)                        # Scroll vers la fin
    log_text.config(state='disabled')        # Rendre readonly
