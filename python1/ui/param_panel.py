# -*- coding: utf-8 -*-
"""程序参数配置页面。"""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config import detection_params, ensure_dirs, load_config, save_config
from core.logger import app_logger
from core.storage import storage


class ParamPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()
        self.load_into_ui()

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        path_box = QGroupBox("存储路径配置")
        path_form = QFormLayout(path_box)

        self.ed_output = QLineEdit()
        self.btn_output = QPushButton("浏览…")
        row1 = QHBoxLayout()
        row1.addWidget(self.ed_output)
        row1.addWidget(self.btn_output)
        path_form.addRow("输出根目录", row1)

        self.ed_log = QLineEdit()
        self.ed_img = QLineEdit()
        self.ed_params = QLineEdit()
        self.ed_db = QLineEdit()
        self.ed_model = QLineEdit()
        self.btn_model = QPushButton("浏览…")
        row_model = QHBoxLayout()
        row_model.addWidget(self.ed_model)
        row_model.addWidget(self.btn_model)

        path_form.addRow("日志子目录名", self.ed_log)
        path_form.addRow("图片子目录名", self.ed_img)
        path_form.addRow("参数子目录名", self.ed_params)
        path_form.addRow("SQLite 路径", self.ed_db)
        path_form.addRow("YOLO 模型", row_model)
        layout.addWidget(path_box)

        det_box = QGroupBox("检测与预处理默认参数")
        form = QFormLayout(det_box)

        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.05, 0.99)
        self.spin_conf.setSingleStep(0.05)
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setRange(0.1, 0.95)
        self.spin_iou.setSingleStep(0.05)
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(320, 1280)
        self.spin_imgsz.setSingleStep(32)
        self.spin_maxdet = QSpinBox()
        self.spin_maxdet.setRange(1, 1000)
        self.spin_lw = QSpinBox()
        self.spin_lw.setRange(1, 20)
        self.spin_sample = QSpinBox()
        self.spin_sample.setRange(1, 30)
        self.chk_labels = QCheckBox("显示类别标签")
        self.chk_conf = QCheckBox("显示置信度")

        self.spin_bright = QSpinBox()
        self.spin_bright.setRange(-100, 100)
        self.spin_contrast = QDoubleSpinBox()
        self.spin_contrast.setRange(0.1, 3.0)
        self.spin_contrast.setSingleStep(0.1)
        self.spin_denoise = QSpinBox()
        self.spin_denoise.setRange(0, 20)
        self.spin_sharpen = QDoubleSpinBox()
        self.spin_sharpen.setRange(0.0, 3.0)
        self.spin_sharpen.setSingleStep(0.1)
        self.chk_clahe = QCheckBox("启用 CLAHE")
        self.spin_rotate = QSpinBox()
        self.spin_rotate.setRange(0, 270)
        self.spin_rotate.setSingleStep(90)
        self.chk_flip_h = QCheckBox("水平翻转")
        self.chk_flip_v = QCheckBox("垂直翻转")

        form.addRow("conf", self.spin_conf)
        form.addRow("iou", self.spin_iou)
        form.addRow("imgsz", self.spin_imgsz)
        form.addRow("max_det", self.spin_maxdet)
        form.addRow("线宽", self.spin_lw)
        form.addRow("视频抽帧间隔", self.spin_sample)
        form.addRow(self.chk_labels)
        form.addRow(self.chk_conf)
        form.addRow("亮度", self.spin_bright)
        form.addRow("对比度", self.spin_contrast)
        form.addRow("去噪强度", self.spin_denoise)
        form.addRow("锐化", self.spin_sharpen)
        form.addRow(self.chk_clahe)
        form.addRow("预处理旋转(°)", self.spin_rotate)
        form.addRow(self.chk_flip_h)
        form.addRow(self.chk_flip_v)
        layout.addWidget(det_box)

        tip = QLabel(
            "说明：输出按日期自动划分到「输出根目录/YYYY-MM-DD/{日志,图片,参数}」；"
            "识别结果与日志也会写入 SQLite。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#94a3b8;")
        layout.addWidget(tip)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_reload = QPushButton("重新加载")
        self.btn_open_root = QPushButton("打开输出目录")
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_reload)
        btns.addWidget(self.btn_open_root)
        btns.addStretch()
        layout.addLayout(btns)
        layout.addStretch()

        self.btn_output.clicked.connect(self._pick_output)
        self.btn_model.clicked.connect(self._pick_model)
        self.btn_save.clicked.connect(self.save_from_ui)
        self.btn_reload.clicked.connect(self.load_into_ui)
        self.btn_open_root.clicked.connect(self._open_root)

    def load_into_ui(self) -> None:
        cfg = load_config()
        self.ed_output.setText(str(cfg.get("output_root", "")))
        self.ed_log.setText(str(cfg.get("log_subdir", "logs")))
        self.ed_img.setText(str(cfg.get("image_subdir", "images")))
        self.ed_params.setText(str(cfg.get("params_subdir", "params")))
        self.ed_db.setText(str(cfg.get("db_path", "")))
        self.ed_model.setText(str(cfg.get("model_path", "")))
        self.spin_conf.setValue(float(cfg.get("conf", 0.25)))
        self.spin_iou.setValue(float(cfg.get("iou", 0.45)))
        self.spin_imgsz.setValue(int(cfg.get("imgsz", 640)))
        self.spin_maxdet.setValue(int(cfg.get("max_det", 300)))
        self.spin_lw.setValue(int(cfg.get("line_width", 2)))
        self.spin_sample.setValue(int(cfg.get("sample_every", 1)))
        self.chk_labels.setChecked(bool(cfg.get("show_labels", True)))
        self.chk_conf.setChecked(bool(cfg.get("show_conf", True)))
        self.spin_bright.setValue(int(cfg.get("brightness", 0)))
        self.spin_contrast.setValue(float(cfg.get("contrast", 1.0)))
        self.spin_denoise.setValue(int(cfg.get("denoise", 0)))
        self.spin_sharpen.setValue(float(cfg.get("sharpen", 0.0)))
        self.chk_clahe.setChecked(bool(cfg.get("clahe", False)))
        self.spin_rotate.setValue(int(cfg.get("rotate", 0)))
        self.chk_flip_h.setChecked(bool(cfg.get("flip_h", False)))
        self.chk_flip_v.setChecked(bool(cfg.get("flip_v", False)))

    def collect(self) -> dict:
        return {
            "output_root": self.ed_output.text().strip(),
            "log_subdir": self.ed_log.text().strip() or "logs",
            "image_subdir": self.ed_img.text().strip() or "images",
            "params_subdir": self.ed_params.text().strip() or "params",
            "db_path": self.ed_db.text().strip(),
            "model_path": self.ed_model.text().strip(),
            "conf": float(self.spin_conf.value()),
            "iou": float(self.spin_iou.value()),
            "imgsz": int(self.spin_imgsz.value()),
            "max_det": int(self.spin_maxdet.value()),
            "line_width": int(self.spin_lw.value()),
            "sample_every": int(self.spin_sample.value()),
            "show_labels": self.chk_labels.isChecked(),
            "show_conf": self.chk_conf.isChecked(),
            "brightness": int(self.spin_bright.value()),
            "contrast": float(self.spin_contrast.value()),
            "denoise": int(self.spin_denoise.value()),
            "sharpen": float(self.spin_sharpen.value()),
            "clahe": self.chk_clahe.isChecked(),
            "rotate": int(self.spin_rotate.value()),
            "flip_h": self.chk_flip_h.isChecked(),
            "flip_v": self.chk_flip_v.isChecked(),
        }

    def save_from_ui(self) -> None:
        cfg = load_config()
        cfg.update(self.collect())
        save_config(cfg)
        ensure_dirs(cfg)
        storage.save_params_snapshot(detection_params(cfg), note="配置页保存")
        app_logger.info(f"配置已保存，输出目录={cfg['output_root']}")
        QMessageBox.information(self, "成功", "配置已保存。")

    def _pick_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择输出根目录", self.ed_output.text())
        if path:
            self.ed_output.setText(path)

    def _pick_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 YOLO 权重", self.ed_model.text(), "模型 (*.pt *.onnx);;所有文件 (*)"
        )
        if path:
            self.ed_model.setText(path)

    def _open_root(self) -> None:
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        root = Path(self.ed_output.text().strip() or load_config()["output_root"])
        root.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(root)))
