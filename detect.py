
video_path = 'C:\\PYGAME\\backgrounds\\OUTPUT\\download\\clip_7.mp4'  # Mets ici ton fichier vidéo


import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import cv2
from PIL import Image
from ultralytics import YOLO
from collections import Counter

# Détecteur YOLO (ou MegaDetector)
detector = YOLO('yolov8n.pt')

# BLIP pour captioning
processor = BlipProcessor.from_pretrained("C:\\PYGAME\\models\\blip")
model = BlipForConditionalGeneration.from_pretrained("C:\\PYGAME\\models\\blip")

# Ouvre la vidéo
cap = cv2.VideoCapture(video_path)


descriptions = []
frame_rate = 0.1  # 1 frame toutes les 2 secondes
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = 1 #int(fps * frame_rate)
frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_count % frame_interval == 0:
        # Détection YOLO sur la frame
        results = detector.predict(source=frame, conf=0.4, verbose=False)

        for res in results:
            for box in res.boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = xyxy
                # Découpe crop précis
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

                # Caption BLIP sur crop
                inputs = processor(images=image, return_tensors="pt")
                out = model.generate(**inputs)
                description = processor.decode(out[0], skip_special_tokens=True)
                descriptions.append(description)
                print(f"Frame {frame_count} description: {description}")

    frame_count += 1

cap.release()

# Synthèse simple : la description la plus fréquente
if descriptions:
    final_desc = Counter(descriptions).most_common(1)[0][0]
    print("\nDescription finale unique pour la vidéo:")
    print(final_desc)
else:
    print("Aucune détection ou description générée.")