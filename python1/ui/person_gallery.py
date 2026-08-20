# -*- coding: utf-8 -*-
"""行人分割 + 二次识别结果画廊。"""

from __future__ import annotations

import cv2
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def _bgr_to_pixmap(bgr: np.ndarray, max_h: int = 200, max_w: int = 220) -> QPixmap:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    pix = QPixmap.fromImage(qimg)
    if pix.height() > max_h or pix.width() > max_w:
        pix = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pix


class PersonCard(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, person: dict, parent=None) -> None:
        super().__init__(parent)
        index = int(person.get("index", 0))
        conf = float(person.get("conf", 0))
        first = float(person.get("first_conf", conf))
        redetected = bool(person.get("redetected"))
        re_n = int(person.get("re_person_count", 0))
        image_bgr = person["image"]
        self.index = index
        acc = conf * 100.0
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(190)
        border = "#34d399" if redetected else "#475569"
        self.setStyleSheet(
            f"QFrame {{ background:#1e293b; border:1px solid {border}; border-radius:8px; }}"
            "QFrame:hover { border-color:#38bdf8; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(f"行人 #{index}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#e2e8f0; border:none; font-size:18px; font-weight:bold;")
        stage = QLabel("二次识别结果" if redetected else "分割预览")
        stage.setAlignment(Qt.AlignCenter)
        stage.setStyleSheet("color:#94a3b8; border:none; font-size:13px;")
        acc_lbl = QLabel(f"准确率  {acc:.1f}%")
        acc_lbl.setAlignment(Qt.AlignCenter)
        color = "#34d399" if conf >= 0.5 else ("#fbbf24" if conf >= 0.35 else "#f87171")
        acc_lbl.setStyleSheet(f"color:{color}; border:none; font-size:20px; font-weight:bold;")
        tip = QLabel(
            f"首次 {first * 100:.1f}% ｜ 复核检出 {re_n}"
            if redetected
            else f"置信度 {conf:.3f}"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet("color:#94a3b8; border:none; font-size:13px;")
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setPixmap(_bgr_to_pixmap(image_bgr))
        img.setStyleSheet("border:none;")
        layout.addWidget(title)
        layout.addWidget(stage)
        layout.addWidget(acc_lbl)
        layout.addWidget(tip)
        layout.addWidget(img)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.index)
        super().mousePressEvent(event)


class PersonGallery(QWidget):
    """横向滚动展示分割并二次识别后的行人。"""

    person_selected = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._persons: list[dict] = []
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.header = QLabel("分割行人二次识别：暂无")
        self.header.setStyleSheet("color:#94a3b8; font-size:16px;")
        root.addWidget(self.header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            "QScrollArea { border:1px solid #334155; background:#0f172a; }"
        )
        self.inner = QWidget()
        self.row = QHBoxLayout(self.inner)
        self.row.setAlignment(Qt.AlignLeft)
        self.row.addStretch()
        self.scroll.setWidget(self.inner)
        root.addWidget(self.scroll)

    def clear(self) -> None:
        self._persons = []
        while self.row.count():
            item = self.row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.row.addStretch()
        self.header.setText("分割行人二次识别：暂无")

    def set_persons(self, persons: list[dict]) -> None:
        self.clear()
        self._persons = persons
        count = len(persons)
        if persons:
            avg = sum(float(p.get("conf", 0)) for p in persons) / count
            re_n = sum(1 for p in persons if p.get("redetected"))
            self.header.setText(
                f"分割并二次识别：共 {count} 人，已复核 {re_n} 人，"
                f"平均准确率 {avg * 100:.1f}%（点击卡片可放大）"
            )
        else:
            self.header.setText("分割行人二次识别：共 0 人")

        while self.row.count():
            item = self.row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not persons:
            tip = QLabel("未检测到行人")
            tip.setStyleSheet("color:#64748b; padding:20px; font-size:18px;")
            self.row.addWidget(tip)
            self.row.addStretch()
            return

        for p in persons:
            card = PersonCard(p)
            card.clicked.connect(self._on_click)
            self.row.addWidget(card)
        self.row.addStretch()

    def _on_click(self, index: int) -> None:
        for p in self._persons:
            if p["index"] == index:
                self.person_selected.emit(p["image"])
                break

    def persons(self) -> list[dict]:
        return list(self._persons)
