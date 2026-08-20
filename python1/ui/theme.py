# -*- coding: utf-8 -*-
"""界面主题、字体与全局样式。"""

from __future__ import annotations

from typing import Any

from config import load_config, save_config

THEMES: dict[str, dict[str, str]] = {
    "深色科技": {
        "bg": "#0b1220",
        "panel": "#0f172a",
        "card": "#1e293b",
        "border": "#334155",
        "text": "#e2e8f0",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "accent_text": "#0b1220",
        "input": "#111827",
        "hover": "#334155",
        "tab_sel": "#0ea5e9",
        "chart_bg": "#0f172a",
        "chart_ax": "#1e293b",
    },
    "浅色清晰": {
        "bg": "#f1f5f9",
        "panel": "#ffffff",
        "card": "#e2e8f0",
        "border": "#94a3b8",
        "text": "#0f172a",
        "muted": "#475569",
        "accent": "#0284c7",
        "accent_text": "#ffffff",
        "input": "#ffffff",
        "hover": "#cbd5e1",
        "tab_sel": "#0284c7",
        "chart_bg": "#f8fafc",
        "chart_ax": "#ffffff",
    },
    "青绿护眼": {
        "bg": "#0c1a17",
        "panel": "#102420",
        "card": "#16352e",
        "border": "#2d6a5a",
        "text": "#e7fff6",
        "muted": "#8fb9aa",
        "accent": "#34d399",
        "accent_text": "#06201a",
        "input": "#0f2a24",
        "hover": "#1f4d44",
        "tab_sel": "#10b981",
        "chart_bg": "#102420",
        "chart_ax": "#16352e",
    },
}

DEFAULT_UI = {
    "theme_name": "深色科技",
    "font_family": "Microsoft YaHei UI",
    "font_size": 18,
    "title_font_size": 20,
    "button_padding": 12,
}


def ui_settings(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    out = dict(DEFAULT_UI)
    for k, v in DEFAULT_UI.items():
        if k in cfg:
            out[k] = cfg[k]
    return out


def theme_colors(cfg: dict[str, Any] | None = None) -> dict[str, str]:
    ui = ui_settings(cfg)
    name = str(ui.get("theme_name", "深色科技"))
    return dict(THEMES.get(name, THEMES["深色科技"]))


def build_stylesheet(cfg: dict[str, Any] | None = None) -> str:
    cfg = cfg or load_config()
    ui = ui_settings(cfg)
    c = theme_colors(cfg)
    font = ui["font_family"]
    fs = int(ui["font_size"])
    ts = int(ui["title_font_size"])
    pad = int(ui["button_padding"])
    return f"""
    QMainWindow, QWidget {{
        background: {c['bg']};
        color: {c['text']};
        font-family: "{font}";
        font-size: {fs}px;
    }}
    QGroupBox {{
        border: 1px solid {c['border']};
        border-radius: 8px;
        margin-top: 14px;
        padding-top: 12px;
        font-size: {ts}px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {c['accent']};
        font-size: {ts}px;
    }}
    QPushButton {{
        background: {c['card']};
        border: 1px solid {c['border']};
        padding: {pad}px {pad + 6}px;
        border-radius: 6px;
        font-size: {fs}px;
        min-height: 28px;
    }}
    QPushButton:hover {{ background: {c['hover']}; }}
    QPushButton:disabled {{ color: {c['muted']}; }}
    QTabWidget::pane {{ border: 1px solid {c['border']}; }}
    QTabBar::tab {{
        background: {c['card']};
        padding: 12px 22px;
        margin-right: 3px;
        border: 1px solid {c['border']};
        font-size: {fs}px;
        min-width: 110px;
        min-height: 32px;
    }}
    QTabBar::tab:selected {{
        background: {c['tab_sel']};
        color: {c['accent_text']};
        font-weight: bold;
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit, QTableWidget {{
        background: {c['input']};
        border: 1px solid {c['border']};
        padding: 6px;
        font-size: {fs}px;
        color: {c['text']};
        selection-background-color: {c['accent']};
    }}
    QHeaderView::section {{
        background: {c['card']};
        color: {c['text']};
        font-size: {fs}px;
        padding: 8px;
    }}
    QLabel {{ font-size: {fs}px; color: {c['text']}; }}
    QStatusBar {{
        background: {c['panel']};
        color: {c['muted']};
        font-size: {fs}px;
    }}
    QToolTip {{
        background: {c['card']};
        color: {c['text']};
        border: 1px solid {c['border']};
        font-size: {fs}px;
    }}
    QScrollBar:vertical {{
        background: {c['panel']};
        width: 12px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 4px;
        min-height: 24px;
    }}
    """


def save_ui_settings(**kwargs: Any) -> dict[str, Any]:
    cfg = load_config()
    for k, v in kwargs.items():
        cfg[k] = v
    save_config(cfg)
    return cfg
