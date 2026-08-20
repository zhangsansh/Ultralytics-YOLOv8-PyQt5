# -*- coding: utf-8 -*-
"""可缩放/平移/旋转的图像查看器。"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QWheelEvent, QMouseEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy


class ImageViewer(QLabel):
    """滚轮缩放、左键拖拽平移、右键旋转 90°。"""

    transformed = pyqtSignal(float, float)  # scale, rotation

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QLabel { background: #0f172a; border: 1px solid #334155; color: #94a3b8; }"
        )
        self.setText("请上传图片或视频")
        self.setMouseTracking(True)

        self._bgr: Optional[np.ndarray] = None
        self._scale = 1.0
        self._rotation = 0.0  # 显示旋转角度（度）
        self._offset = QPoint(0, 0)
        self._dragging = False
        self._last_pos = QPoint()
        self._fit = True

    def clear_image(self) -> None:
        self._bgr = None
        self._scale = 1.0
        self._rotation = 0.0
        self._offset = QPoint(0, 0)
        self._fit = True
        self.setText("请上传图片或视频")
        self.setPixmap(QPixmap())

    def set_image(self, image_bgr: np.ndarray, reset_view: bool = True) -> None:
        self._bgr = image_bgr.copy()
        if reset_view:
            self._scale = 1.0
            self._rotation = 0.0
            self._offset = QPoint(0, 0)
            self._fit = True
        self._render()

    def current_image(self) -> Optional[np.ndarray]:
        return None if self._bgr is None else self._bgr.copy()

    def reset_view(self) -> None:
        self._scale = 1.0
        self._rotation = 0.0
        self._offset = QPoint(0, 0)
        self._fit = True
        self._render()

    def rotate_by(self, degrees: float) -> None:
        self._rotation = (self._rotation + degrees) % 360
        self._fit = False
        self._render()
        self.transformed.emit(self._scale, self._rotation)

    def zoom_to(self, scale: float) -> None:
        self._scale = max(0.1, min(8.0, scale))
        self._fit = False
        self._render()
        self.transformed.emit(self._scale, self._rotation)

    def _rotated(self, img: np.ndarray) -> np.ndarray:
        angle = self._rotation
        if abs(angle) < 1e-6:
            return img
        h, w = img.shape[:2]
        center = (w / 2.0, h / 2.0)
        matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])
        nw = int(h * sin + w * cos)
        nh = int(h * cos + w * sin)
        matrix[0, 2] += (nw / 2) - center[0]
        matrix[1, 2] += (nh / 2) - center[1]
        return cv2.warpAffine(img, matrix, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(15, 23, 42))

    def _to_qpixmap(self, bgr: np.ndarray) -> QPixmap:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        return QPixmap.fromImage(qimg)

    def _render(self) -> None:
        if self._bgr is None:
            return
        img = self._rotated(self._bgr)
        pix = self._to_qpixmap(img)

        if self._fit:
            scaled = pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._scale = scaled.width() / max(1, pix.width())
            self.setPixmap(scaled)
        else:
            target_w = max(1, int(pix.width() * self._scale))
            target_h = max(1, int(pix.height() * self._scale))
            scaled = pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # 画布 + 偏移
            canvas = QPixmap(self.size())
            canvas.fill(Qt.transparent)
            from PyQt5.QtGui import QPainter

            painter = QPainter(canvas)
            x = (self.width() - scaled.width()) // 2 + self._offset.x()
            y = (self.height() - scaled.height()) // 2 + self._offset.y()
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.setPixmap(canvas)
        self.transformed.emit(self._scale, self._rotation)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._bgr is not None:
            self._render()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._bgr is None:
            return
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        self._fit = False
        self.zoom_to(self._scale * factor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._bgr is not None:
            self._dragging = True
            self._fit = False
            self._last_pos = event.pos()
        elif event.button() == Qt.RightButton and self._bgr is not None:
            self.rotate_by(90)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            delta = event.pos() - self._last_pos
            self._last_pos = event.pos()
            self._offset += delta
            self._render()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)
