# ============================================================
#  download_model.py  –  Downloads the hand landmark model
#  Run once before main.py
# ============================================================
import urllib.request
import os

MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "hand_landmarker.task"

if os.path.exists(MODEL_PATH):
    print(f"Model already exists: {MODEL_PATH}")
else:
    print("Downloading hand landmark model (~10 MB)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print(f"Done → {MODEL_PATH}")