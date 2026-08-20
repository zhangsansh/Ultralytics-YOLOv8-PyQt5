# -*- coding: utf-8 -*-
"""主窗口：识别大屏 / 日志 / 图表 / 配置。"""

from __future__ import annotations

from typing import Optional

import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from config import detection_params, ensure_dirs, load_config, save_config
from core.detector import detector
from core.image_io import is_image, is_video, read_image
from core.logger import app_logger
from core.storage import storage
from ui.chart_panel import ChartPanel
from ui.help_panel import HelpPanel
from ui.image_viewer import ImageViewer
from ui.log_panel import LogPanel
from ui.param_panel import ParamPanel
from ui.person_gallery import PersonGallery
from ui.theme import build_stylesheet, ui_settings
from ui.theme_panel import ThemePanel


class DetectWorker(QThread):
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int, object)

    def __init__(self, kind: str, path: str, params: dict, image: Optional[np.ndarray] = None):
        super().__init__()
        self.kind = kind
        self.path = path
        self.params = params
        self.image = image
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            detector.load()
            if self.kind == "image":
                assert self.image is not None
                result = detector.detect_image(self.image, self.params, source_path=self.path)
            else:
                result = detector.detect_video(
                    self.path,
                    self.params,
                    progress_cb=lambda i, t, img: self.progress.emit(i, t, img),
                    cancel_flag=lambda: self._cancel,
                )
            self.finished_ok.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class DetectPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._source_path = ""
        self._source_bgr: Optional[np.ndarray] = None
        self._worker: Optional[DetectWorker] = None
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        tools = QHBoxLayout()
        self.btn_open = QPushButton("上传图片/视频")
        self.btn_detect = QPushButton("开始识别")
        self.btn_save = QPushButton("手动保存当前图")
        self.btn_full = QPushButton("返回整图")
        self.btn_reset = QPushButton("重置视图")
        self.btn_rot_l = QPushButton("左转90°")
        self.btn_rot_r = QPushButton("右转90°")
        self.btn_cancel = QPushButton("取消视频识别")
        self.btn_cancel.setEnabled(False)
        for b in (
            self.btn_open, self.btn_detect, self.btn_save, self.btn_full,
            self.btn_reset, self.btn_rot_l, self.btn_rot_r, self.btn_cancel,
        ):
            tools.addWidget(b)
        left_layout.addLayout(tools)

        hint = QLabel("鼠标：滚轮缩放 · 左键拖拽平移 · 右键旋转90° ｜ 下方为分割出的行人，点击可放大")
        hint.setStyleSheet("color:#94a3b8;")
        left_layout.addWidget(hint)

        mid_split = QSplitter(Qt.Vertical)
        self.viewer = ImageViewer()
        mid_split.addWidget(self.viewer)

        self.gallery = PersonGallery()
        mid_split.addWidget(self.gallery)
        mid_split.setStretchFactor(0, 4)
        mid_split.setStretchFactor(1, 1)
        left_layout.addWidget(mid_split, 1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        left_layout.addWidget(self.progress)

        self.view_info = QLabel("缩放: 100%  旋转: 0°")
        self.view_info.setStyleSheet("color:#64748b;")
        left_layout.addWidget(self.view_info)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        param_box = QGroupBox("识别参数（本次运行）")
        form = QFormLayout(param_box)
        cfg = load_config()

        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.05, 0.99)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setValue(float(cfg.get("conf", 0.25)))
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setRange(0.1, 0.95)
        self.spin_iou.setSingleStep(0.05)
        self.spin_iou.setValue(float(cfg.get("iou", 0.45)))
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(320, 1280)
        self.spin_imgsz.setSingleStep(32)
        self.spin_imgsz.setValue(int(cfg.get("imgsz", 640)))
        self.spin_lw = QSpinBox()
        self.spin_lw.setRange(1, 20)
        self.spin_lw.setValue(int(cfg.get("line_width", 2)))
        self.spin_sample = QSpinBox()
        self.spin_sample.setRange(1, 30)
        self.spin_sample.setValue(int(cfg.get("sample_every", 1)))
        self.chk_labels = QCheckBox("显示标签")
        self.chk_labels.setChecked(bool(cfg.get("show_labels", True)))
        self.chk_conf = QCheckBox("显示置信度")
        self.chk_conf.setChecked(bool(cfg.get("show_conf", True)))
        self.spin_bright = QSpinBox()
        self.spin_bright.setRange(-100, 100)
        self.spin_bright.setValue(int(cfg.get("brightness", 0)))
        self.spin_contrast = QDoubleSpinBox()
        self.spin_contrast.setRange(0.1, 3.0)
        self.spin_contrast.setSingleStep(0.1)
        self.spin_contrast.setValue(float(cfg.get("contrast", 1.0)))
        self.spin_rotate = QSpinBox()
        self.spin_rotate.setRange(0, 270)
        self.spin_rotate.setSingleStep(90)
        self.spin_rotate.setValue(int(cfg.get("rotate", 0)))

        form.addRow("置信度阈值", self.spin_conf)
        form.addRow("IoU", self.spin_iou)
        form.addRow("输入尺寸", self.spin_imgsz)
        form.addRow("线宽", self.spin_lw)
        form.addRow("视频抽帧", self.spin_sample)
        form.addRow(self.chk_labels)
        form.addRow(self.chk_conf)
        form.addRow("亮度", self.spin_bright)
        form.addRow("对比度", self.spin_contrast)
        form.addRow("预处理旋转", self.spin_rotate)
        right_layout.addWidget(param_box)

        stats_box = QGroupBox("识别结果 / 准确率分析")
        stats_layout = QVBoxLayout(stats_box)
        self.lbl_stats = QLabel("尚未识别")
        self.lbl_stats.setWordWrap(True)
        self.lbl_stats.setStyleSheet("color:#e2e8f0; font-size:17px;")
        stats_layout.addWidget(self.lbl_stats)
        right_layout.addWidget(stats_box)

        history_box = QGroupBox("最近识别记录")
        hist_layout = QVBoxLayout(history_box)
        self.lbl_history = QLabel("")
        self.lbl_history.setWordWrap(True)
        self.lbl_history.setStyleSheet("color:#94a3b8;")
        hist_layout.addWidget(self.lbl_history)
        right_layout.addWidget(history_box)
        right_layout.addStretch()
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        self.btn_open.clicked.connect(self.open_file)
        self.btn_detect.clicked.connect(self.start_detect)
        self.btn_save.clicked.connect(self.manual_save)
        self.btn_full.clicked.connect(self.show_full_result)
        self.btn_reset.clicked.connect(self.viewer.reset_view)
        self.btn_rot_l.clicked.connect(lambda: self.viewer.rotate_by(-90))
        self.btn_rot_r.clicked.connect(lambda: self.viewer.rotate_by(90))
        self.btn_cancel.clicked.connect(self.cancel_detect)
        self.viewer.transformed.connect(self._on_transform)
        self.gallery.person_selected.connect(self._on_person_selected)
        self._last_annotated = None
        self.refresh_history()

    def _on_person_selected(self, image_bgr) -> None:
        """点击分割行人时，在主视图临时放大查看（不覆盖原主图备份）。"""
        if image_bgr is None:
            return
        self.viewer.set_image(image_bgr, reset_view=True)
        app_logger.info("主图切换为选中的分割行人预览（可再次识别或重新上传恢复整图）")

    def _on_transform(self, scale: float, rotation: float) -> None:
        self.view_info.setText(f"缩放: {scale * 100:.0f}%  旋转: {rotation:.0f}°")

    def current_params(self) -> dict:
        cfg = load_config()
        params = detection_params(cfg)
        params.update(
            {
                "conf": float(self.spin_conf.value()),
                "iou": float(self.spin_iou.value()),
                "imgsz": int(self.spin_imgsz.value()),
                "line_width": int(self.spin_lw.value()),
                "sample_every": int(self.spin_sample.value()),
                "show_labels": self.chk_labels.isChecked(),
                "show_conf": self.chk_conf.isChecked(),
                "brightness": int(self.spin_bright.value()),
                "contrast": float(self.spin_contrast.value()),
                "rotate": int(self.spin_rotate.value()),
            }
        )
        return params

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片或视频",
            "",
            "媒体文件 (*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.avi *.mov *.mkv);;所有文件 (*)",
        )
        if not path:
            return
        self._source_path = path
        if is_image(path):
            img = read_image(path)
            if img is None:
                QMessageBox.warning(self, "错误", "无法读取图片")
                return
            self._source_bgr = img
            self.viewer.set_image(img)
            self.gallery.clear()
            app_logger.info(f"已加载图片: {path}")
        elif is_video(path):
            self._source_bgr = None
            # 取首帧预览
            import cv2

            cap = cv2.VideoCapture(path)
            ok, frame = cap.read()
            cap.release()
            if ok:
                self.viewer.set_image(frame)
            self.gallery.clear()
            app_logger.info(f"已加载视频: {path}")
        else:
            QMessageBox.warning(self, "错误", "不支持的文件类型")

    def start_detect(self) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "正在识别中…")
            return
        if not self._source_path:
            QMessageBox.information(self, "提示", "请先上传图片或视频")
            return

        params = self.current_params()
        # 同步写入全局配置，便于其它页面一致
        cfg = load_config()
        cfg.update({k: params[k] for k in params})
        save_config(cfg)

        if is_image(self._source_path):
            if self._source_bgr is None:
                self._source_bgr = read_image(self._source_path)
            kind = "image"
            image = self._source_bgr
        elif is_video(self._source_path):
            kind = "video"
            image = None
        else:
            QMessageBox.warning(self, "错误", "不支持的文件类型")
            return

        app_logger.info(f"开始识别 ({kind}): {self._source_path}")
        self.btn_detect.setEnabled(False)
        self.btn_cancel.setEnabled(kind == "video")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self._worker = DetectWorker(kind, self._source_path, params, image)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.progress.connect(self._on_progress)
        self._worker.start()

    def cancel_detect(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_progress(self, i: int, total: int, img) -> None:
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(min(i, total))
        if isinstance(img, np.ndarray):
            self.viewer.set_image(img, reset_view=False)

    def _on_done(self, result: dict) -> None:
        self.btn_detect.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(False)
        annotated = result.get("annotated")
        if annotated is not None:
            self.viewer.set_image(annotated)
            self._last_annotated = annotated

        persons = result.get("persons") or []
        self.gallery.set_persons(persons)

        stats = result.get("stats", {})
        confs = [b["conf"] for b in result.get("boxes", [])]
        conf_text = ""
        if confs:
            conf_text = (
                f"\n各目标准确率: "
                + ", ".join(f"{c * 100:.1f}%" for c in confs[:20])
                + (" …" if len(confs) > 20 else "")
            )
        mask_n = sum(1 for p in persons if p.get("used_mask"))
        re_n = sum(1 for p in persons if p.get("redetected"))
        re_text = ""
        if persons:
            re_text = (
                "\n二次识别准确率: "
                + ", ".join(
                    f"#{p.get('index')}={float(p.get('conf', 0)) * 100:.1f}%"
                    for p in persons[:20]
                )
                + (" …" if len(persons) > 20 else "")
            )
        self.lbl_stats.setText(
            f"行人数量: {stats.get('person_count', 0)}\n"
            f"已分割并二次识别: {len(persons)} 人"
            f"（复核 {re_n}，掩膜 {mask_n}）\n"
            f"整图平均准确率: {stats.get('avg_conf', 0) * 100:.1f}%\n"
            f"二次识别平均准确率: {stats.get('re_avg_conf', 0) * 100:.1f}%\n"
            f"最高/最低准确率: {stats.get('max_conf', 0) * 100:.1f}% / "
            f"{stats.get('min_conf', 0) * 100:.1f}%\n"
            f"耗时: {stats.get('duration_ms', 0):.1f} ms\n"
            f"整图结果: {result.get('result_path', '')}"
            f"{conf_text}{re_text}"
        )
        app_logger.info(
            f"识别完成: 人数={stats.get('person_count', 0)}, "
            f"平均置信度={stats.get('avg_conf', 0):.3f}, "
            f"二次识别={len(persons)}, 二次平均={stats.get('re_avg_conf', 0):.3f}"
        )
        self.refresh_history()

    def show_full_result(self) -> None:
        img = getattr(self, "_last_annotated", None)
        if img is not None:
            self.viewer.set_image(img, reset_view=True)

    def _on_fail(self, msg: str) -> None:
        self.btn_detect.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(False)
        app_logger.error(f"识别失败: {msg}")
        QMessageBox.critical(self, "识别失败", msg)

    def manual_save(self) -> None:
        img = self.viewer.current_image()
        if img is None:
            QMessageBox.information(self, "提示", "当前没有可保存的图片")
            return
        path = storage.save_result_image(img, source_path=self._source_path, suffix="manual")
        app_logger.info(f"手动保存图片: {path}")
        QMessageBox.information(self, "已保存", str(path))

    def refresh_history(self) -> None:
        runs = storage.list_runs(8)
        if not runs:
            self.lbl_history.setText("暂无记录")
            return
        lines = []
        for r in runs:
            lines.append(
                f"#{r['id']} {r['created_at']} | {r['source_type']} | "
                f"人数={r['person_count']} | 准确率={float(r['avg_conf']) * 100:.1f}%"
            )
        self.lbl_history.setText("\n".join(lines))

    def sync_params_from_config(self) -> None:
        cfg = load_config()
        self.spin_conf.setValue(float(cfg.get("conf", 0.25)))
        self.spin_iou.setValue(float(cfg.get("iou", 0.45)))
        self.spin_imgsz.setValue(int(cfg.get("imgsz", 640)))
        self.spin_lw.setValue(int(cfg.get("line_width", 2)))
        self.spin_sample.setValue(int(cfg.get("sample_every", 1)))
        self.chk_labels.setChecked(bool(cfg.get("show_labels", True)))
        self.chk_conf.setChecked(bool(cfg.get("show_conf", True)))
        self.spin_bright.setValue(int(cfg.get("brightness", 0)))
        self.spin_contrast.setValue(float(cfg.get("contrast", 1.0)))
        self.spin_rotate.setValue(int(cfg.get("rotate", 0)))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("行人识别可视化大屏 · YOLOv8 + PyQt5")
        self.resize(1480, 920)
        self.apply_style()

        self.tabs = QTabWidget()
        self.detect_page = DetectPage()
        self.log_page = LogPanel()
        self.chart_page = ChartPanel()
        self.param_page = ParamPanel()
        self.theme_page = ThemePanel()
        self.help_page = HelpPanel()
        self.tabs.addTab(self.detect_page, "① 行人识别")
        self.tabs.addTab(self.log_page, "② 日志记录")
        self.tabs.addTab(self.chart_page, "③ 图表分析")
        self.tabs.addTab(self.param_page, "④ 参数配置")
        self.tabs.addTab(self.theme_page, "⑤ 外观设置")
        self.tabs.addTab(self.help_page, "⑥ 使用说明")
        self.setCentralWidget(self.tabs)
        self.setStatusBar(QStatusBar())
        ui = ui_settings()
        self.statusBar().showMessage(
            f"就绪 · YOLOv8 开源 · 主题:{ui['theme_name']} · 字号:{ui['font_size']}"
        )

        self.tabs.currentChanged.connect(self._on_tab)
        self.theme_page.style_changed.connect(self.apply_style)
        app_logger.info("应用启动")

    def apply_style(self) -> None:
        self.setStyleSheet(build_stylesheet())
        ui = ui_settings()
        if self.statusBar():
            self.statusBar().showMessage(
                f"外观已应用 · 主题:{ui['theme_name']} · 字体:{ui['font_family']} · 字号:{ui['font_size']}"
            )
        # 图表页按主题刷新配色
        if hasattr(self, "chart_page"):
            try:
                self.chart_page.refresh_charts()
            except Exception:
                pass

    def _on_tab(self, idx: int) -> None:
        if idx == 0:
            self.detect_page.sync_params_from_config()
            self.detect_page.refresh_history()
        elif idx == 1:
            self.log_page.refresh_db_logs()
        elif idx == 2:
            self.chart_page.refresh_charts()
        elif idx == 3:
            self.param_page.load_into_ui()
        elif idx == 4:
            self.theme_page.load_into_ui()


def run_app() -> int:
    ensure_dirs()
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.QtGui import QFont

    # QWebEngine 需在创建 QApplication 之前设置
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    # 提前导入 WebEngine，避免后续导入顺序问题
    import PyQt5.QtWebEngineWidgets  # noqa: F401

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("行人识别可视化大屏")
    ui = ui_settings()
    app.setFont(QFont(str(ui["font_family"]), int(ui["font_size"])))
    win = MainWindow()
    win.show()
    return app.exec_()
