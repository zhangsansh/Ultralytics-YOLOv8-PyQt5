# -*- coding: utf-8 -*-
"""图像读写辅助。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


def is_image(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_video(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTS


def read_image(path: str) -> Optional[np.ndarray]:
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img


def write_image(path: str, image_bgr: np.ndarray) -> bool:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    ext = Path(path).suffix or ".jpg"
    ok, buf = cv2.imencode(ext, image_bgr)
    if not ok:
        return False
    buf.tofile(path)
    return True


def bgr_to_rgb(image_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
