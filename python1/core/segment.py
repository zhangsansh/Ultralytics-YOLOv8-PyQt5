# -*- coding: utf-8 -*-
"""从检测结果中分割/裁剪行人，并支持二次识别标注。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _clamp_box(x1: int, y1: int, x2: int, y2: int, w: int, h: int) -> tuple[int, int, int, int]:
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w, x2))
    y2 = max(0, min(h, y2))
    if x2 <= x1:
        x2 = min(w, x1 + 1)
    if y2 <= y1:
        y2 = min(h, y1 + 1)
    return x1, y1, x2, y2


_FONT_CACHE: dict[int, Any] = {}


def _cn_font(size: int):
    size = max(12, int(size))
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                font = ImageFont.truetype(str(path), size=size)
                _FONT_CACHE[size] = font
                return font
            except Exception:
                continue
    font = ImageFont.load_default()
    _FONT_CACHE[size] = font
    return font


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0]), int(box[3] - box[1])


def extract_persons(
    image_bgr: np.ndarray,
    boxes: list[dict[str, Any]],
    yolo_result=None,
    pad_ratio: float = 0.04,
    annotate: bool = False,
) -> list[dict[str, Any]]:
    """
    将每个检出行人分割出来（默认返回干净裁剪图，便于二次识别）。
    annotate=True 时直接在图上画首次准确率。
    """
    h, w = image_bgr.shape[:2]
    masks = None
    if yolo_result is not None and getattr(yolo_result, "masks", None) is not None:
        try:
            masks = yolo_result.masks.data.cpu().numpy()
        except Exception:
            masks = None

    persons: list[dict[str, Any]] = []
    for i, b in enumerate(boxes):
        x1, y1, x2, y2 = map(int, (b["x1"], b["y1"], b["x2"], b["y2"]))
        bw, bh = x2 - x1, y2 - y1
        px = int(bw * pad_ratio)
        py = int(bh * pad_ratio)
        x1, y1, x2, y2 = _clamp_box(x1 - px, y1 - py, x2 + px, y2 + py, w, h)

        crop = image_bgr[y1:y2, x1:x2].copy()
        used_mask = False

        if masks is not None and i < len(masks):
            mask = masks[i]
            if mask.shape[0] != h or mask.shape[1] != w:
                mask = cv2.resize(mask.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
            m = (mask > 0.5).astype(np.uint8)
            m_crop = m[y1:y2, x1:x2]
            if m_crop.size and m_crop.max() > 0:
                bg = np.full_like(crop, (20, 24, 36))
                m3 = m_crop[:, :, None]
                crop = np.where(m3 > 0, crop, bg)
                used_mask = True

        conf = float(b.get("conf", 0))
        person = {
            "index": i + 1,
            "conf": conf,
            "accuracy": conf * 100.0,
            "first_conf": conf,
            "bbox": (x1, y1, x2, y2),
            "image": crop,
            "raw_image": crop.copy(),
            "used_mask": used_mask,
            "redetected": False,
            "re_boxes": [],
        }
        if annotate:
            person["image"] = annotate_person_image(crop, person)
        persons.append(person)
    return persons


def annotate_person_image(crop_bgr: np.ndarray, person: dict[str, Any]) -> np.ndarray:
    """
    在分割图上完整显示准确率文字（Pillow 中文字体）。
    顶部/底部预留标题栏，必要时加宽画布，避免文字被裁切。
    """
    idx = int(person.get("index", 0))
    conf = float(person.get("conf", 0))
    first = float(person.get("first_conf", conf))
    redetected = bool(person.get("redetected"))
    acc_pct = conf * 100.0

    if redetected:
        label = f"#{idx} 二次识别 {acc_pct:.1f}%"
        sub = f"首次 {first * 100:.1f}%"
    else:
        label = f"#{idx} 准确率 {acc_pct:.1f}%"
        sub = ""

    h0, w0 = crop_bgr.shape[:2]
    font_size = max(16, min(28, int(max(w0, 120) * 0.12)))
    font = _cn_font(font_size)
    sub_font = _cn_font(max(14, font_size - 4))

    probe = Image.new("RGB", (8, 8))
    probe_draw = ImageDraw.Draw(probe)
    tw, th = _text_size(probe_draw, label, font)
    sw, sh = _text_size(probe_draw, sub, sub_font) if sub else (0, 0)

    while tw + 24 > max(w0, 180) and font_size > 14:
        font_size -= 1
        font = _cn_font(font_size)
        sub_font = _cn_font(max(12, font_size - 4))
        tw, th = _text_size(probe_draw, label, font)
        sw, sh = _text_size(probe_draw, sub, sub_font) if sub else (0, 0)

    pad_top = th + (sh + 14 if sub else 12) + 12
    pad_bottom = 18
    need_w = max(w0, tw + 28, sw + 24, 200)
    canvas = np.zeros((h0 + pad_top + pad_bottom, need_w, 3), dtype=np.uint8)
    canvas[:] = (15, 23, 42)
    x_off = (need_w - w0) // 2
    canvas[pad_top:pad_top + h0, x_off:x_off + w0] = crop_bgr

    bar_y0 = canvas.shape[0] - pad_bottom
    cv2.rectangle(canvas, (0, bar_y0), (need_w, canvas.shape[0]), (30, 30, 30), -1)
    fill_w = int(need_w * max(0.0, min(1.0, conf)))
    color = (40, 200, 80) if conf >= 0.5 else ((0, 180, 255) if conf >= 0.35 else (60, 60, 220))
    cv2.rectangle(canvas, (0, bar_y0), (fill_w, canvas.shape[0]), color, -1)

    banner = (40, 200, 120) if redetected else (0, 170, 220)
    cv2.rectangle(canvas, (0, 0), (need_w, pad_top), banner, -1)

    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil)
    draw.text((12, 8), label, font=font, fill=(15, 15, 15))
    if sub:
        draw.text((12, 8 + th + 6), sub, font=sub_font, fill=(35, 35, 35))
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)


def draw_redetect_boxes(
    crop_bgr: np.ndarray,
    boxes: list[dict[str, Any]],
    params: dict[str, Any] | None = None,
) -> np.ndarray:
    """在二次识别结果上绘制检测框；框上短标签，完整中文准确率由 annotate 显示。"""
    params = params or {}
    out = crop_bgr.copy()
    lw = max(1, int(params.get("line_width", 2)))
    for b in boxes:
        x1, y1, x2, y2 = map(int, (b["x1"], b["y1"], b["x2"], b["y2"]))
        cv2.rectangle(out, (x1, y1), (x2, y2), (50, 220, 120), lw)
        label = f"{float(b.get('conf', 0)) * 100:.1f}%"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        y_text = max(th + 6, y1 - 4)
        x_text = min(x1, max(0, out.shape[1] - tw - 6))
        cv2.rectangle(out, (x_text, y_text - th - 4), (x_text + tw + 4, y_text + 2), (50, 220, 120), -1)
        cv2.putText(
            out, label, (x_text + 2, y_text),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 1, cv2.LINE_AA,
        )
    return out
