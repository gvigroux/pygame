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
            "-framerate", "50",
            "-f", "gdigrab",
            "-draw_mouse", "0",
            "-i", f"title={window_title}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "output.mp4"
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
