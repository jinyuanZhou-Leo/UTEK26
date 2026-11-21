from __future__ import annotations

import logging
import time
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from sentinel.sensors.vision import camera

logger = logging.getLogger(__name__)

# where the google landmark model is
MODEL_PATH = Path(__file__).resolve().parents[4] / "models" / "face_landmarker.task"


def get_landmarker() -> vision.FaceLandmarker:
    """Create an Google FaceLandmarker instance"""
    # Reference: https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker#video_4
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,  
        output_facial_transformation_matrixes=True,
    )
    return vision.FaceLandmarker.create_from_options(options)


def detect(landmarker: vision.FaceLandmarker, rgb_frame) -> vision.FaceLandmarkerResult:
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    return landmarker.detect_for_video(img, int(time.monotonic() * 1000))
