# -*- coding: utf-8 -*-
"""
行人识别可视化大屏
技术栈: Ultralytics YOLOv8（开源）+ PyQt5 + Matplotlib + OpenCV

运行（推荐 Anaconda）:
  E:\\Anconda3\\python.exe main.py
或:
  python main.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ensure_dirs


def main():
    ensure_dirs()
    from ui.main_window import run_app

    sys.exit(run_app())


if __name__ == "__main__":
    main()
