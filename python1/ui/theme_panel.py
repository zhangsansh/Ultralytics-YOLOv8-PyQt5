# -*- coding: utf-8 -*-
"""字体 / 主题 / 样式调整页面。"""

from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config import load_config
from core.logger import app_logger
from ui.theme import THEMES, save_ui_settings, ui_settings


class ThemePanel(QWidget):
    style_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()
        self.load_into_ui()

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        box = QGroupBox("字体与主题")
        form = QFormLayout(box)

        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(list(THEMES.keys()))

        self.cmb_font = QComboBox()
        self.cmb_font.addItems(
            [
                "Microsoft YaHei UI",
                "Microsoft YaHei",
                "SimHei",
                "SimSun",
                "DengXian",
                "Arial",
                "Segoe UI",
            ]
        )
        self.cmb_font.setEditable(True)

        self.spin_font = QSpinBox()
        self.spin_font.setRange(12, 32)
        self.spin_title = QSpinBox()
        self.spin_title.setRange(14, 36)
        self.spin_pad = QSpinBox()
        self.spin_pad.setRange(4, 24)

        form.addRow("主题", self.cmb_theme)
        form.addRow("字体", self.cmb_font)
        form.addRow("正文字号", self.spin_font)
        form.addRow("标题字号", self.spin_title)
        form.addRow("按钮内边距", self.spin_pad)
        layout.addWidget(box)

        preview = QGroupBox("效果预览")
        pv = QVBoxLayout(preview)
        self.lbl_preview = QLabel("预览文字：行人识别可视化大屏 · 准确率 87.5%")
        self.lbl_preview.setWordWrap(True)
        self.btn_preview = QPushButton("预览按钮样式")
        pv.addWidget(self.lbl_preview)
        pv.addWidget(self.btn_preview)
        layout.addWidget(preview)

        tip = QLabel(
            "说明：增大字号可提升大屏可读性；浅色主题适合明亮环境；"
            "点击「应用并保存」后立即生效，并写入 app_config.json。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#94a3b8;")
        layout.addWidget(tip)

        btns = QHBoxLayout()
        self.btn_apply = QPushButton("应用并保存")
        self.btn_reload = QPushButton("重新加载")
        self.btn_reset = QPushButton("恢复默认")
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_reload)
        btns.addWidget(self.btn_reset)
        btns.addStretch()
        layout.addLayout(btns)
        layout.addStretch()

        self.btn_apply.clicked.connect(self.apply)
        self.btn_reload.clicked.connect(self.load_into_ui)
        self.btn_reset.clicked.connect(self.reset_default)
        self.spin_font.valueChanged.connect(self._update_preview)
        self.cmb_font.currentTextChanged.connect(self._update_preview)

    def load_into_ui(self) -> None:
        ui = ui_settings(load_config())
        idx = self.cmb_theme.findText(str(ui["theme_name"]))
        if idx >= 0:
            self.cmb_theme.setCurrentIndex(idx)
        self.cmb_font.setCurrentText(str(ui["font_family"]))
        self.spin_font.setValue(int(ui["font_size"]))
        self.spin_title.setValue(int(ui["title_font_size"]))
        self.spin_pad.setValue(int(ui["button_padding"]))
        self._update_preview()

    def _update_preview(self) -> None:
        family = self.cmb_font.currentText().strip() or "Microsoft YaHei UI"
        size = self.spin_font.value()
        self.lbl_preview.setStyleSheet(
            f'font-family:"{family}"; font-size:{size + 2}px; color:#e2e8f0;'
        )

    def apply(self) -> None:
        save_ui_settings(
            theme_name=self.cmb_theme.currentText(),
            font_family=self.cmb_font.currentText().strip() or "Microsoft YaHei UI",
            font_size=int(self.spin_font.value()),
            title_font_size=int(self.spin_title.value()),
            button_padding=int(self.spin_pad.value()),
        )
        app_logger.info(
            f"外观已更新: 主题={self.cmb_theme.currentText()}, "
            f"字体={self.cmb_font.currentText()}, 字号={self.spin_font.value()}"
        )
        self.style_changed.emit()
        QMessageBox.information(self, "成功", "外观设置已应用。")

    def reset_default(self) -> None:
        save_ui_settings(
            theme_name="深色科技",
            font_family="Microsoft YaHei UI",
            font_size=18,
            title_font_size=20,
            button_padding=12,
        )
        self.load_into_ui()
        self.style_changed.emit()
        app_logger.info("外观已恢复默认")
