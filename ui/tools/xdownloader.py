
import os
import queue
import threading
from tkinter import filedialog
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import snscrape.modules.twitter as sntwitter
from twscrape import API, gather
from playwright.sync_api import sync_playwright
import time
import vlc

import ssl
import urllib3
import requests
from PIL import Image, ImageTk
import requests
from io import BytesIO
import asyncio
import httpx
import webbrowser
from twscrape import API, gather

from ui.log import log_message

cacert_path = r"C:/Users/gvigroux/AppData/Local/Programs/Python/Python313/Lib/site-packages/certifi/cacert_thales.pem"

# Sauvegarde des init originaux
_orig_transport_init = httpx.AsyncHTTPTransport.__init__
_orig_client_init = httpx.AsyncClient.__init__

def patched_transport_init(self, *args, **kwargs):
    print("[PATCH] AsyncHTTPTransport.__init__ called")
    # Forcer proxy et désactiver SSL verify
    kwargs['proxy'] = "http://127.0.0.1:9000"
    kwargs['verify'] = cacert_path
    _orig_transport_init(self, *args, **kwargs)

def patched_client_init(self, *args, **kwargs):
    print("[PATCH] AsyncClient.__init__ called")
    # Si aucun transport n'est donné, utiliser celui patché avec proxy+verify=False
    if 'transport' not in kwargs:
        kwargs['transport'] = httpx.AsyncHTTPTransport()
    # Forcer verify False (au cas où)
    kwargs['verify'] = cacert_path
    # Timeout confortable
    kwargs['timeout'] = 60.0
    _orig_client_init(self, *args, **kwargs)

# Appliquer les patchs
httpx.AsyncHTTPTransport.__init__ = patched_transport_init
httpx.AsyncClient.__init__ = patched_client_init


THUMBNAIL_SIZE = (160, 90)

class XDownloader:
    def __init__(self, state) :
        self.state = state
        self.current_player = None
        self.current_video_frame = None
        self.thumbs = []
        self.thumbnail_queue = queue.Queue()
        #self.on_double_click = on_double_click

        # Crée la fenêtre Toplevel
        self.window = ttk.Toplevel()
        self.window.title("Library")

        # Dimensions
        window_width = 1000
        window_height = 700
        screen_width = self.state['app'].winfo_screenwidth()
        screen_height = self.state['app'].winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Partie gauche (thumbnails + scroll)
        left_side = ttk.Frame(self.window)
        left_side.pack(side="left", fill="both", expand=True)

        self.thumbs_canvas = ttk.Canvas(left_side)
        scrollbar = ttk.Scrollbar(left_side, orient="vertical", command=self.thumbs_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.thumbs_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumbs_canvas.configure(scrollregion=self.thumbs_canvas.bbox("all"))
        )

        def _on_mousewheel(event):
            self.thumbs_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.thumbs_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.thumbs_canvas.bind_all("<Button-4>", lambda e: self.thumbs_canvas.yview_scroll(-1, "units"))
        self.thumbs_canvas.bind_all("<Button-5>", lambda e: self.thumbs_canvas.yview_scroll(1, "units"))

        self.thumbs_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.thumbs_canvas.configure(yscrollcommand=scrollbar.set)

        self.thumbs_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Partie droite (lecteur vidéo)
        self.video_frame = ttk.Frame(self.window, width=304, height=540)
        self.video_frame.pack(side="right", padx=10, pady=10)
        self.video_frame.pack_propagate(False)

        video_label = ttk.Label(self.video_frame)
        video_label.pack(expand=True)

       # Lancer le thread
        #self.start_x_loader("filter:videos min_faves:1000 min_retweets:1000 min_replies:500 since:2025-07-17 lang:fr")
        posts = self.scrape_9gag_hot()
        print(f"Found {len(posts)} posts.")

    def start_x_loader(self, research  ):
        thread = threading.Thread(target=self.load_thumbnails, args=(research,), daemon=True)
        thread.start()

    def start_9gag_loader(self, research  ):
        pass
        

                
    def scrape_9gag_hot(self, max_posts=20):
        posts = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
                headless=True,
                args=["--incognito"]
            )

            page = browser.new_page()

            # Désactive navigator.webdriver AVANT le goto
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print("Navigating to 9GAG Hot...")
            page.goto("https://9gag.com/top", timeout=30000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)


     

            print("Scroll to trigger lazy load...")
            for _ in range(2):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(2000)

            ##########################################
            # Click sur le bouton 'Accept' dans l'iframe
            # Récupérer le frame par son URL (ou partie de l’URL)
            frame = None
            for f in page.frames:
                if "cdn.privacy-mgmt.com/index.html" in f.url:
                    frame = f
                    break

            if frame is None:
                print("Iframe pas trouvée")
            else:
                print("Iframe trouvée, tentative de clic...")

                # Attendre et cliquer sur le bouton 'Accept' dans cette iframe
                btn = frame.wait_for_selector("button[title='Accept']", state="visible", timeout=10000)
                btn.click()
                print("Bouton 'Accept' cliqué dans l'iframe")


            try:
                print("Try wait_for_selector('article')...")
                page.wait_for_selector("article", timeout=15000)
                print("Article found!")
            except Exception:
                print("Timeout, no article found.")
                html = page.content()
                with open("debug_9gag.html", "w", encoding="utf-8") as f:
                    f.write(html)
                browser.close()
                return posts

            last_count = 0
            scrolls = 0
            while len(posts) < max_posts and scrolls < 5:
                print(f"Scroll #{scrolls+1}")
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(3000)
                scrolls += 1

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                for article in soup.find_all("article"):
                    post_id = article.get("id")
                    if not post_id or any(p["id"] == post_id for p in posts):
                        continue

                    title_tag = article.find("h2")
                    title = title_tag.get_text(strip=True) if title_tag else "No title"

                    link_tag = article.find("a", href=True)
                    url = "https://9gag.com" + link_tag["href"] if link_tag else "No link"

                    # Vidéo: souvent pas direct
                    video_url = None
                    video_tag = article.find("video")
                    if video_tag:
                        video_url = video_tag.get("src")

                    thumb_tag = article.find("img")
                    thumb_url = thumb_tag["src"] if thumb_tag else None

                    posts.append({
                        "id": post_id,
                        "title": title,
                        "url": url,
                        "video_url": video_url,
                        "thumb_url": thumb_url
                    })

                    if len(posts) >= max_posts:
                        break

            browser.close()
        return posts

        
    def scrape_9gag_hot2(self):
        url = "https://9gag.com/hot"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, verify=cacert_path) #
        soup = BeautifulSoup(response.text, "html.parser")

        posts = []
        for article in soup.find_all("article"):
            title = article.find("h2")
            if title:
                title_text = title.get_text(strip=True)
            else:
                title_text = "No title"

            link = article.find("a", href=True)
            if link:
                post_url = "https://9gag.com" + link["href"]
            else:
                post_url = "No link"

            posts.append({
                "title": title_text,
                "url": post_url
            })

        return posts


    def load_thumbnails(self, research):
        videos = asyncio.run(self.get_all_video_files(research))
        log_message(self.state, f"Found {len(videos)} videos.")
        for video in videos:
            thumb = self.download_and_resize_thumbnail(video["thumb"])
            self.add_thumbnail(thumb, video)
            #thumb = self.extract_thumbnail(video_path)
            #duration = self.get_video_duration(video_path)
            #if thumb:
            #    self.thumbnail_queue.put((thumb, video_path, duration))
            pass

    def download_and_resize_thumbnail(self, url, size=THUMBNAIL_SIZE):
        response = requests.get(url, verify=cacert_path)  # ou `verify=cacert_path`
        response.raise_for_status()
        image_data = response.content

        image = Image.open(BytesIO(image_data))
        image = image.resize(size, Image.LANCZOS)

        return ImageTk.PhotoImage(image)

    def add_thumbnail(self, thumb, video, columns=8):
        self.thumbs.append(thumb)

        i = len(self.thumbs) - 1
        row = i // columns
        col = i % columns

        frame = ttk.Frame(self.scrollable_frame, padding=5)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nw")

        label_img = ttk.Label(frame, image=thumb)
        label_img.image = thumb
        label_img.pack()

        click_id = None  # pour stocker le timer de clic

        def on_click(e, path=video["url"]):
            nonlocal click_id
            if click_id is not None:
                self.window.after_cancel(click_id)
                click_id = None
                if self.on_double_click:
                    self.on_double_click(path)
            else:
                click_id = self.window.after(250, lambda: self.play_video_vlc(self.state, path))

        label_img.bind("<Button-1>", on_click)

        # # Nom du fichier
        # ttk.Label(frame, text=os.path.basename(video_path), wraplength=150).pack()

        # # Durée
        # ttk.Label(frame, text=duration, font=("Arial", 8, "italic")).pack()
        
    async def get_all_video_files(self, research):
        videos = []
        api = API()
        tweets = await gather(api.search(research, limit=20))
        for tweet in tweets:
            print(tweet.rawContent)

            media = getattr(tweet, "media", None)
            if media:
                # Si media est une liste, sinon on le met dans une liste pour itérer
                medias = media if isinstance(media, list) else [media]
                
                if media.videos:
                    vid = media.videos[0]
                    # Essaye d'afficher la vraie URL vidéo
                    url = getattr(vid, "mediaUrl", None)
                    thumb = getattr(vid, "thumbnailUrl", None)
                    if not url and hasattr(vid, "variants"):
                        # Certains objets media ont des variants (qualités vidéo)
                        variants = vid.variants
                        if variants:
                            url = variants[0].url  # prend la première variante
                    print("URL vidéo:", url if url else "Pas d'URL vidéo")
                    videos.append({"url": url, "thumb": thumb})
        return videos

       
    def play_video_vlc(self, state, video_path):
        log_message(state, f"Play video [{video_path}]")
        if self.current_player:
            self.current_player.stop()
            self.current_player.release()
            self.current_player = None
        if self.current_video_frame:
            self.current_video_frame.destroy()
            self.current_video_frame = None

        self.current_video_frame = ttk.Frame(self.video_frame, width=304, height=540)
        self.current_video_frame.pack()

        instance = vlc.Instance()
        player = instance.media_player_new()

        handle = self.current_video_frame.winfo_id()
        media = instance.media_new(video_path)
        player.set_media(media)
        player.set_hwnd(handle)  # Windows only

        player.play()
        self.current_player = player


        
    def on_close(self):
        # Met à jour la config
        #self.state["config"]["downloader"]["url"]   = self.url_entry.get()
        #self.state["config"]["downloader"]["split"] = self.split_entry.get()

        # Détruire la fenêtre
        self.window.destroy()

       