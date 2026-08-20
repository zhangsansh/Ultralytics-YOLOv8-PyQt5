# -*- coding: utf-8 -*-
"""日志页面。"""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)

from config import day_dirs, load_config
from core.logger import app_logger
from core.storage import storage


class LogPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()
        app_logger.add_ui_hook(self._on_log)

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        tip = QLabel("实时操作日志（同时写入按日期划分的日志文件与 SQLite）")
        tip.setStyleSheet("color:#94a3b8;")
        layout.addWidget(tip)

        tools = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新数据库日志")
        self.btn_open = QPushButton("打开今日日志文件")
        self.btn_clear = QPushButton("清空显示")
        self.btn_open_images = QPushButton("打开今日识别图片目录")
        for b in (self.btn_refresh, self.btn_open, self.btn_clear, self.btn_open_images):
            tools.addWidget(b)
        tools.addStretch()
        layout.addLayout(tools)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet(
            "QTextEdit { background:#0b1220; color:#e2e8f0; font-family: Consolas, monospace; }"
        )
        layout.addWidget(self.text, 2)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["时间", "日期", "级别", "内容"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        pal = self.table.palette()
        pal.setColor(QPalette.Base, QColor("#0b1220"))
        pal.setColor(QPalette.AlternateBase, QColor("#111827"))
        pal.setColor(QPalette.Text, QColor("#e2e8f0"))
        pal.setColor(QPalette.HighlightedText, QColor("#f8fafc"))
        pal.setColor(QPalette.Highlight, QColor("#1e3a5f"))
        self.table.setPalette(pal)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #0b1220;
                color: #e2e8f0;
                gridline-color: #1e293b;
                border: 1px solid #334155;
                outline: none;
            }
            QTableWidget::item {
                background-color: #0b1220;
                color: #e2e8f0;
                padding: 4px;
                border: none;
            }
            QTableWidget::item:alternate {
                background-color: #111827;
                color: #e2e8f0;
            }
            QTableWidget::item:selected {
                background-color: #1e3a5f;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #e2e8f0;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
                padding: 6px;
            }
            QTableCornerButton::section {
                background-color: #1e293b;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #0b1220;
            }
            """
        )
        layout.addWidget(self.table, 2)

        self.btn_refresh.clicked.connect(self.refresh_db_logs)
        self.btn_open.clicked.connect(self.open_today_log)
        self.btn_clear.clicked.connect(self.text.clear)
        self.btn_open_images.clicked.connect(self.open_today_images)

        self.refresh_db_logs()

    def _on_log(self, level: str, line: str) -> None:
        self.text.append(line)
        try:
            storage.add_operation_log(level, line)
        except Exception:
            pass

    def refresh_db_logs(self) -> None:
        rows = storage.list_logs(500)
        self.table.setRowCount(len(rows))
        fg = QColor("#e2e8f0")
        for i, r in enumerate(rows):
            values = [
                str(r.get("created_at", "")),
                str(r.get("day", "")),
                str(r.get("level", "")),
                str(r.get("message", "")),
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setForeground(fg)
                self.table.setItem(i, col, item)

    def open_today_log(self) -> None:
        path = app_logger.log_path()
        if path.exists():
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl

            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            QMessageBox.information(self, "提示", f"日志尚不存在:\n{path}")

    def open_today_images(self) -> None:
        dirs = day_dirs(load_config())
        path = dirs["images"]
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
