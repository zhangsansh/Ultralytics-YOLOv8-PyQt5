# -*- coding: utf-8 -*-
"""图像预处理：亮度/对比度/去噪/锐化/CLAHE/旋转翻转。"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def apply_preprocess(bgr: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    img = bgr.copy()

    rotate = int(params.get("rotate", 0)) % 360
    if rotate == 90:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rotate == 180:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rotate == 270:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if params.get("flip_h"):
        img = cv2.flip(img, 1)
    if params.get("flip_v"):
        img = cv2.flip(img, 0)

    brightness = int(params.get("brightness", 0))
    contrast = float(params.get("contrast", 1.0))
    if brightness != 0 or abs(contrast - 1.0) > 1e-6:
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

    denoise = int(params.get("denoise", 0))
    if denoise > 0:
        strength = max(1, denoise)
        img = cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)

    if params.get("clahe"):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    sharpen = float(params.get("sharpen", 0.0))
    if sharpen > 0:
        blur = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(img, 1.0 + sharpen, blur, -sharpen, 0)

    return img
