import asyncio
import httpx
import webbrowser
from twscrape import API, gather

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

async def main():
    api = API()

    tweets = await gather(api.search("filter:videos min_faves:100 lang:en", limit=10))
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
                #if( url ):                    
                #    webbrowser.open(url)
            else:
                print("Pas de vidéo dans media")
        else:
            print("Pas de média")

asyncio.run(main())
