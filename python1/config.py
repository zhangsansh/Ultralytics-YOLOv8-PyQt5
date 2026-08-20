# -*- coding: utf-8 -*-
"""全局配置：路径、检测默认参数、读写。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "app_config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "output_root": str(ROOT / "outputs"),
    "log_subdir": "logs",
    "image_subdir": "images",
    "params_subdir": "params",
    "db_path": str(ROOT / "outputs" / "db" / "pedestrian.db"),
    "model_path": str(ROOT / "yolov8n.pt"),
    "conf": 0.25,
    "iou": 0.45,
    "imgsz": 640,
    "max_det": 300,
    "line_width": 2,
    "sample_every": 1,
    "show_labels": True,
    "show_conf": True,
    "brightness": 0,
    "contrast": 1.0,
    "denoise": 0,
    "sharpen": 0.0,
    "clahe": False,
    "rotate": 0,
    "flip_h": False,
    "flip_v": False,
    # 界面
    "theme_name": "深色科技",
    "font_family": "Microsoft YaHei UI",
    "font_size": 18,
    "title_font_size": 20,
    "button_padding": 12,
}


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def ensure_dirs(cfg: dict[str, Any] | None = None) -> None:
    cfg = cfg or load_config()
    root = Path(cfg["output_root"])
    for key in ("log_subdir", "image_subdir", "params_subdir"):
        (root / cfg[key]).mkdir(parents=True, exist_ok=True)
    Path(cfg["db_path"]).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "models").mkdir(parents=True, exist_ok=True)


def day_dirs(cfg: dict[str, Any] | None = None, day: str | None = None) -> dict[str, Path]:
    """按日期划分：outputs/YYYY-MM-DD/{logs,images,params}"""
    from datetime import date

    cfg = cfg or load_config()
    day = day or date.today().isoformat()
    base = Path(cfg["output_root"]) / day
    paths = {
        "base": base,
        "logs": base / cfg["log_subdir"],
        "images": base / cfg["image_subdir"],
        "params": base / cfg["params_subdir"],
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def detection_params(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    keys = (
        "conf", "iou", "imgsz", "max_det", "line_width", "sample_every",
        "show_labels", "show_conf", "brightness", "contrast", "denoise",
        "sharpen", "clahe", "rotate", "flip_h", "flip_v",
    )
    return {k: cfg[k] for k in keys if k in cfg}
