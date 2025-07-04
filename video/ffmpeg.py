import subprocess
import threading

class RecorderFFMPEG:

    def __init__(self, window_size):
        self.audio_process = None
        self.video_process = None

        window_title = "pygame window"

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-framerate", "60",
            "-f", "gdigrab",
            "-draw_mouse", "0",
            "-i", f"title={window_title}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "output.mp4"
        ]

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-framerate", "60",
            "-f", "gdigrab",
            "-draw_mouse", "0",
            "-i", f"title={window_title}",
            "-f", "dshow",
            "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-crf", "18",  # Ajout du contrôle de qualité (18-28 est une bonne plage)
            "-pix_fmt", "yuv420p",  # Format de pixel compatible
            "-movflags", "+faststart",  # Pour streaming web
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-filter_complex", "[1:a]adelay=1000|1000[outa]",  # Synchronisation audio si nécessaire
            "-map", "0:v",  # Mapper explicitement les flux
            "-map", "[outa]",
            "-shortest",  # Terminer quand la vidéo finit
            "output.mp4"
        ]

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            # Capture vidéo (écran)
            "-f", "gdigrab",
            "-framerate", "60",
            "-draw_mouse", "0",
            "-i", f"title={window_title}",
            
            # Capture audio (VB-Cable)
            "-thread_queue_size", "2048",  # Augmenté pour plus de stabilité
            "-f", "dshow",
            "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",
            
            # Paramètres vidéo
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            
            # Paramètres audio avec correction de délai
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            
            # Synchronisation explicite
            "-af", "asetpts=N/SR/TB",  # Réinitialise les timestamps audio
            "-vsync", "1",  # Synchronisation frame-by-frame
            
            # Option alternative (si le délai est constant) :
            # "-filter_complex", "[1:a]adelay=500|500[outa]",  # Délai en ms
            
            "-map", "0:v",
            "-map", "1:a",
            
            # Ajustement temporel global
            "-copyts",  # Conserve les timestamps originaux
            "-muxdelay", "0",  # Délai de multiplexage nul
            "-muxpreload", "0", 
            
            "output.mp4"
        ]
                
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            
            # 1. CAPTURE VIDÉO (avec paramètres optimisés)
            "-f", "gdigrab",
            "-framerate", "60",
            "-thread_queue_size", "4096",  # Augmenté pour stabilité
            "-draw_mouse", "1",
            "-i", f"title={window_title}",
            
            # 2. CAPTURE AUDIO (avec paramètres temps-réel)
            "-f", "dshow",
            "-thread_queue_size", "4096",
            "-audio_buffer_size", "100",  # Réduit la latence
            "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",
            
            # 3. PARAMÈTRES DE SYNCHRONISATION CRITIQUES
            "-async", "1000",  # Force la synchronisation
            "-vsync", "passthrough",  # Garde les FPS originaux
            "-copyts",  # Préserve les timestamps
            "-start_at_zero",  # Synchronise au démarrage
            
            # 4. FILTRES DE SYNCHRO AVANCÉS
            "-filter_complex", 
            "[1:a]aresample=async=1000,asetpts=N/SR/TB[audio_out];" + 
            "[0:v]setpts=N/FRAME_RATE/TB[video_out]",
            
            # 5. ENCODAGE (optimisé pour synchronisation)
            "-map", "[video_out]",
            "-map", "[audio_out]",
            "-c:v", "libx264",
            "-preset", "ultrafast",  # Minimise la latence
            "-tune", "zerolatency",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-fflags", "+genpts",  # Régénère les timestamps
            
            # 6. FORMAT DE SORTIE
            "-f", "mp4",
            "-movflags", "+faststart",
            "output_synced.mp4"
        ]        


        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            
            # 1. Configuration de base
            "-flush_packets", "1",  # Force l'écriture immédiate des paquets
            "-fflags", "+genpts+igndts",  # Régénère les PTS et ignore les DTS problématiques
            
            # 2. Capture vidéo
            "-f", "gdigrab",
            "-framerate", "60",
            "-thread_queue_size", "8192",  # Augmenté pour stabilité
            "-draw_mouse", "1",
            "-i", f"title={window_title}",
            
            # 3. Capture audio
            "-f", "dshow",
            "-thread_queue_size", "8192",
            "-audio_buffer_size", "50",  # Buffer réduit pour moins de latence
            "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",
            
            # 4. Paramètres de synchronisation critiques
            "-use_wallclock_as_timestamps", "1",  # Utilise l'horloge système réelle
            "-vsync", "2",  # Mode 'passthrough' amélioré
            "-async", "1",  # Mode de synchronisation strict
            
            # 5. Filtres de correction
            "-filter_complex", 
            "[1:a]aresample=async=1000:first_pts=0,asetpts=N/SR/TB[audio];" +
            "[0:v]setpts='if(eq(N,0),0,PTS+1/TB)'[video]",
            
            # 6. Encodage
            "-map", "[video]",
            "-map", "[audio]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-x264opts", "force-cfr=1",  # Force le mode CFR
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            
            # 7. Paramètres de sortie
            "-max_interleave_delta", "0",  # Évite le réordonnancement
            "-avoid_negative_ts", "make_zero",  # Corrige les timestamps négatifs
            "-f", "mp4",
            "output_fixed.mp4"
        ]

        #"-thread_queue_size", "512",
        #"-f", "dshow",
        #"-i", "audio=CABLE Output (VB-Audio Virtual Cable)", #CABLE Output (VB-Audio Virtual Cable)   #Stereo Mix (Realtek(R) Audio)"
        #"-c:a", "aac",
        #"-b:a", "128k",
        #"-ar", "44100",

        # ffmpeg_audio_cmd = [
        #     "ffmpeg", "-y",
        #     "-f", "dshow",
        #     "-i", "audio=Stereo Mix (Realtek(R) Audio)",
        #     "-ar", "44100",
        #     "-ac", "2",
        #     "-c:a", "pcm_s16le",
        #     "output.mp4"
        # ]
            
        # ffmpeg_video_cmd = [
        #     "ffmpeg", "-y",
        #     "-f", "gdigrab",
        #     "-framerate", "60",
        #     "-i", "title=NomDeTaFenetre",
        #     "-c:v", "libx264",
        #     "-preset", "ultrafast",
        #     "-tune", "zerolatency",
        #     "-crf", "23",
        #     "-pix_fmt", "yuv420p",
        #     "output.mp4"
        # ]
        # self.audio_process = subprocess.Popen(
        #                     ffmpeg_audio_cmd,
        #                     stdin=subprocess.PIPE,
        #                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        
        self.video_process = subprocess.Popen(
                             ffmpeg_cmd,
                             stdin=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        threading.Thread(target=self.wait_for_ffmpeg_ready, args=(self.video_process,), daemon=True).start()
        
                
        # self.audio_thread = threading.Thread(target=self.capture_audio)
        # self.video_thread = threading.Thread(target=self.capture_video)
                
        # self.audio_thread.start()
        # self.video_thread.start()
        # print("audio and video thread started")


    def write(self, pygame, screen, frame_count):
        pass

    def capture_audio(self):
        self.audio_thread = subprocess.Popen([
                "ffmpeg", "-y",
                "-f", "dshow",
                "-i", "audio=CABLE Output (VB-Audio Virtual Cable)", #CABLE Output (VB-Audio Virtual Cable)   #Stereo Mix (Realtek(R) Audio)"
                "-ar", "44100",
                "-ac", "2",
                "-c:a", "pcm_s16le",
                "audio.wav"
                ],
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    def capture_video(self):
        self.video_thread = subprocess.Popen([
                "ffmpeg", "-y",
                "-f", "gdigrab",
                "-framerate", "60",
                "-i", "title=pygame window",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "video.mp4"
            ],
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    def wait_for_ffmpeg_ready(process):
        while True:
            line = process.stderr.readline()
            if not line:
                break
            decoded = line.decode('utf-8').strip()
            print(decoded)  # Debug
            if "Press [q] to stop" in decoded or "frame=" in decoded:
                print("FFmpeg is ready.")
                break

    def stop(self):


        # if( self.audio_thread == None ):
        #     return
        # try:
        #     self.audio_thread.stdin.write(b"q")
        #     self.audio_thread.stdin.flush()

        #     self.video_thread.stdin.write(b"q")
        #     self.video_thread.stdin.flush()

        #     self.audio_thread.wait()
        #     self.video_thread.wait()
        # except:
        #     pass

        if( self.video_process == None ):
            return
        try:
            self.video_process.stdin.write(b"q")
            self.video_process.stdin.flush()
            self.video_process.wait()
        except:
            pass
