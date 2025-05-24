from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, ImageClip, concatenate_videoclips
)

# --- Paramètres ---
RESOLUTION = (1080, 1920)  # Format TikTok (vertical)
FPS = 30
DUREE_MAX = 59  # TikTok max duration (1 minute)

# --- Charger les vidéos ---
video = VideoFileClip("gameplay.mp4").resize(height=RESOLUTION[1])
video = video.set_position("center").set_fps(FPS).subclip(0, min(video.duration, DUREE_MAX))

try:
    intro = VideoFileClip("intro.mp4").resize(height=RESOLUTION[1]).set_fps(FPS)
except:
    intro = None

# --- Charger la musique ---
audio = AudioFileClip("audio.mp3").subclip(0, video.duration + (intro.duration if intro else 0))

# --- Charger le logo ---
try:
    logo = (ImageClip("logo.png")
            .set_duration(video.duration + (intro.duration if intro else 0))
            .resize(width=200)
            .set_pos(("right", "top")))
except:
    logo = None

# --- Assembler vidéo ---
final_clips = [intro, video] if intro else [video]
full_video = concatenate_videoclips(final_clips, method="compose")

# --- Ajouter overlay/logo ---
video_with_overlay = CompositeVideoClip([full_video, logo] if logo else [full_video], size=RESOLUTION)

# --- Ajouter audio ---
video_with_audio = video_with_overlay.set_audio(audio)

# --- Export ---
video_with_audio.write_videofile(
    "tiktok_ready.mp4",
    codec="libx264",
    audio_codec="aac",
    fps=FPS,
    threads=4,
    preset="ultrafast"
)
