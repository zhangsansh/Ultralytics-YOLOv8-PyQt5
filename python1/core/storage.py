# -*- coding: utf-8 -*-
"""SQLite 与按日期的结果文件存储。"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

from config import day_dirs, load_config
from core.logger import app_logger


class Storage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        cfg = load_config()
        self.db_path = Path(db_path or cfg["db_path"])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS detection_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    day TEXT NOT NULL,
                    source_path TEXT,
                    source_type TEXT,
                    result_image_path TEXT,
                    person_count INTEGER DEFAULT 0,
                    avg_conf REAL DEFAULT 0,
                    max_conf REAL DEFAULT 0,
                    min_conf REAL DEFAULT 0,
                    duration_ms REAL DEFAULT 0,
                    params_json TEXT,
                    note TEXT
                );
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    class_id INTEGER,
                    class_name TEXT,
                    conf REAL,
                    x1 REAL, y1 REAL, x2 REAL, y2 REAL,
                    FOREIGN KEY(run_id) REFERENCES detection_runs(id)
                );
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    day TEXT NOT NULL,
                    level TEXT,
                    message TEXT
                );
                """
            )

    def save_params_snapshot(self, params: dict[str, Any], note: str = "") -> Path:
        dirs = day_dirs()
        stamp = datetime.now().strftime("%H%M%S")
        path = dirs["params"] / f"params_{stamp}.json"
        payload = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": note,
            "params": params,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        app_logger.info(f"参数已保存: {path}")
        return path

    def save_result_image(
        self,
        image_bgr: np.ndarray,
        source_path: str = "",
        suffix: str = "det",
    ) -> Path:
        dirs = day_dirs()
        stamp = datetime.now().strftime("%H%M%S")
        src = Path(source_path) if source_path else None
        if src and src.exists():
            digest = hashlib.md5(src.read_bytes()).hexdigest()
            name = f"{digest}_{suffix}_{stamp}.jpg"
        else:
            name = f"{suffix}_{stamp}.jpg"
        out = dirs["images"] / name
        cv2.imwrite(str(out), image_bgr)
        app_logger.info(f"识别结果图已保存: {out}")
        return out

    def add_operation_log(self, level: str, message: str) -> None:
        now = datetime.now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO operation_logs(created_at, day, level, message) VALUES(?,?,?,?)",
                (now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d"), level, message),
            )

    def save_run(
        self,
        *,
        source_path: str,
        source_type: str,
        result_image_path: str,
        boxes: list[dict[str, Any]],
        duration_ms: float,
        params: dict[str, Any],
        note: str = "",
    ) -> int:
        confs = [float(b["conf"]) for b in boxes]
        avg_conf = float(np.mean(confs)) if confs else 0.0
        max_conf = float(max(confs)) if confs else 0.0
        min_conf = float(min(confs)) if confs else 0.0
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO detection_runs(
                    created_at, day, source_path, source_type, result_image_path,
                    person_count, avg_conf, max_conf, min_conf, duration_ms, params_json, note
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    day,
                    source_path,
                    source_type,
                    result_image_path,
                    len(boxes),
                    avg_conf,
                    max_conf,
                    min_conf,
                    duration_ms,
                    json.dumps(params, ensure_ascii=False),
                    note,
                ),
            )
            run_id = int(cur.lastrowid)
            for b in boxes:
                conn.execute(
                    """
                    INSERT INTO detections(run_id, class_id, class_name, conf, x1, y1, x2, y2)
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        run_id,
                        b.get("class_id", 0),
                        b.get("class_name", "person"),
                        float(b["conf"]),
                        float(b["x1"]),
                        float(b["y1"]),
                        float(b["x2"]),
                        float(b["y2"]),
                    ),
                )
        app_logger.info(
            f"数据库已写入 run_id={run_id}, 人数={len(boxes)}, 平均置信度={avg_conf:.3f}"
        )
        return run_id

    def list_runs(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM detection_runs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def list_logs(self, limit: int = 500) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def run_stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            runs = conn.execute(
                """
                SELECT day, COUNT(*) AS cnt, SUM(person_count) AS persons,
                       AVG(avg_conf) AS avg_conf
                FROM detection_runs GROUP BY day ORDER BY day
                """
            ).fetchall()
            conf_hist = conn.execute(
                "SELECT conf FROM detections ORDER BY id DESC LIMIT 5000"
            ).fetchall()
            recent = conn.execute(
                """
                SELECT person_count, avg_conf, created_at FROM detection_runs
                ORDER BY id DESC LIMIT 30
                """
            ).fetchall()
        return {
            "by_day": [dict(r) for r in runs],
            "confidences": [float(r["conf"]) for r in conf_hist],
            "recent": [dict(r) for r in recent],
        }


storage = Storage()
