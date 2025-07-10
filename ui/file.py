import re
import unicodedata

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
