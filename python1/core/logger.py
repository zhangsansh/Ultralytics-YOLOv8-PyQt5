# -*- coding: utf-8 -*-
"""按日期写入的应用日志 + UI 回调。"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from config import day_dirs, load_config


class AppLogger:
    def __init__(self) -> None:
        self._ui_hooks: list[Callable[[str, str], None]] = []
        self._logger = logging.getLogger("pedestrian_app")
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()
        self._file_handler: Optional[logging.FileHandler] = None
        self._day: Optional[str] = None
        self._refresh_file_handler()

    def add_ui_hook(self, fn: Callable[[str, str], None]) -> None:
        self._ui_hooks.append(fn)

    def _refresh_file_handler(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if self._day == today and self._file_handler is not None:
            return
        if self._file_handler is not None:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()
        dirs = day_dirs(load_config(), today)
        log_path = dirs["logs"] / f"app_{today}.log"
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        self._logger.addHandler(fh)
        self._file_handler = fh
        self._day = today

    def _emit(self, level: str, msg: str) -> None:
        self._refresh_file_handler()
        getattr(self._logger, level.lower(), self._logger.info)(msg)
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] [{level}] {msg}"
        for hook in list(self._ui_hooks):
            try:
                hook(level, line)
            except Exception:
                pass

    def info(self, msg: str) -> None:
        self._emit("INFO", msg)

    def warning(self, msg: str) -> None:
        self._emit("WARNING", msg)

    def error(self, msg: str) -> None:
        self._emit("ERROR", msg)

    def log_path(self) -> Path:
        self._refresh_file_handler()
        dirs = day_dirs(load_config(), self._day)
        return dirs["logs"] / f"app_{self._day}.log"


app_logger = AppLogger()
