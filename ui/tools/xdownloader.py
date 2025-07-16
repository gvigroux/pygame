
import threading
from tkinter import filedialog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import snscrape.modules.twitter as sntwitter

import ssl
import urllib3
import requests

# Monkey patch ssl to disable cert verification globally
def unsafe_ssl_context(*args, **kwargs):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

ssl._create_default_https_context = unsafe_ssl_context

# Disable urllib3 SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey patch requests.Session to disable SSL
original_request = requests.Session.request
def unsafe_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, *args, **kwargs)

requests.Session.request = unsafe_request

# ✅ Now import snscrape (after patches are applied)
import snscrape.modules.twitter as sntwitter


class XDownloader:
    def __init__(self, state) :
        self.state = state

        # Crée la fenêtre Toplevel
        self.window = ttk.Toplevel()
        self.window.title("X")

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
              
        query = "filter:videos lang:fr min_faves:100"
        limit = 10

        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break
            print(f"\nTweet by @{tweet.user.username}")
            print(f"Likes: {tweet.likeCount}")
            print(f"Content: {tweet.content}")
            print(f"Link: https://x.com/{tweet.user.username}/status/{tweet.id}")



        
    def on_close(self):
        # Met à jour la config
        #self.state["config"]["downloader"]["url"]   = self.url_entry.get()
        #self.state["config"]["downloader"]["split"] = self.split_entry.get()

        # Détruire la fenêtre
        self.window.destroy()

       