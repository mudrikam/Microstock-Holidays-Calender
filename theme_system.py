import json
import os
from pathlib import Path


_THEME_PATH = Path(__file__).parent / "configs" / "theme.json"
_theme_data = {}


def _load():
    global _theme_data
    try:
        with open(_THEME_PATH, "r", encoding="utf-8") as f:
            _theme_data = json.load(f)
    except Exception:
        _theme_data = {}


_load()


def reload():
    _load()


def get(section: str, key: str, fallback=None):
    return _theme_data.get(section, {}).get(key, fallback)


def color(key: str) -> str:
    return _theme_data.get("colors", {}).get(key, "#ffffff")


def radius(key: str) -> int:
    return _theme_data.get("radius", {}).get(key, 8)


def glow(key: str) -> str:
    return _theme_data.get("glow", {}).get(key, "none")


def font_size(key: str) -> int:
    val = _theme_data.get("font", {}).get(key, 12)
    try:
        return max(1, int(val))
    except (TypeError, ValueError):
        return 12


def font_family() -> str:
    return _theme_data.get("font", {}).get("family", "Segoe UI")


def spacing(key: str) -> int:
    return _theme_data.get("spacing", {}).get(key, 8)


def opacity(key: str) -> float:
    return _theme_data.get("opacity", {}).get(key, 1.0)


def build_stylesheet() -> str:
    c = _theme_data.get("colors", {})
    r = _theme_data.get("radius", {})
    f = _theme_data.get("font", {})

    return f"""
QWidget {{
    background-color: {c.get('background', '#0d0d0d')};
    color: {c.get('text_primary', '#f0f0f0')};
    font-family: "{f.get('family', 'Segoe UI')}";
    font-size: {f.get('size_normal', 12)}px;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {c.get('background', '#0d0d0d')};
}}

QSplitter::handle {{
    background-color: {c.get('border', '#2a2a2a')};
    width: 2px;
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {c.get('accent', '#ff6a00')};
}}

QTabWidget::pane {{
    background-color: {c.get('surface', '#161616')};
    border: 1px solid {c.get('border', '#2a2a2a')};
    border-radius: {r.get('medium', 8)}px;
}}

QTabBar::tab {{
    background-color: {c.get('tab_bg', '#141414')};
    color: {c.get('text_secondary', '#999999')};
    padding: 8px 20px;
    border: 1px solid {c.get('border', '#2a2a2a')};
    border-bottom: none;
    border-top-left-radius: {r.get('small', 4)}px;
    border-top-right-radius: {r.get('small', 4)}px;
    font-size: {f.get('size_medium', 13)}px;
}}

QTabBar::tab:selected {{
    background-color: {c.get('tab_active', '#1e1e1e')};
    color: {c.get('accent', '#ff6a00')};
    border-bottom: 2px solid {c.get('tab_border', '#ff6a00')};
}}

QTabBar::tab:hover {{
    background-color: {c.get('surface_raised', '#1e1e1e')};
    color: {c.get('text_primary', '#f0f0f0')};
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 1px 2px 1px;
}}

QScrollBar::handle:vertical {{
    background-color: {c.get('scrollbar_handle', '#3d3d3d')};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c.get('scrollbar_handle_hover', '#ff6a00')};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {c.get('accent_pressed', '#cc5500')};
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    width: 0;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 6px;
    border-radius: 3px;
    margin: 1px 2px 1px 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c.get('scrollbar_handle', '#3d3d3d')};
    border-radius: 3px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c.get('scrollbar_handle_hover', '#ff6a00')};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {c.get('accent_pressed', '#cc5500')};
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    height: 0;
    width: 0;
}}

QLineEdit {{
    background-color: {c.get('input_bg', '#1a1a1a')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('input_border', '#333333')};
    border-radius: {r.get('small', 4)}px;
    padding: 6px 10px;
    font-size: {f.get('size_normal', 12)}px;
    selection-background-color: {c.get('accent_dim', '#4d2000')};
}}

QLineEdit:focus {{
    border: 1px solid {c.get('input_focus', '#ff6a00')};
}}

QLineEdit:hover {{
    border: 1px solid {c.get('border_accent', '#ff6a00')};
}}

QComboBox {{
    background-color: {c.get('input_bg', '#1a1a1a')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('input_border', '#333333')};
    border-radius: {r.get('small', 4)}px;
    padding: 5px 10px;
    font-size: {f.get('size_normal', 12)}px;
    min-width: 120px;
}}

QComboBox:hover {{
    border: 1px solid {c.get('accent', '#ff6a00')};
}}

QComboBox:focus {{
    border: 1px solid {c.get('input_focus', '#ff6a00')};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {c.get('surface_raised', '#1e1e1e')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('border', '#2a2a2a')};
    selection-background-color: {c.get('accent_dim', '#4d2000')};
    selection-color: {c.get('accent', '#ff6a00')};
    outline: none;
    padding: 2px;
}}

QPushButton {{
    background-color: {c.get('accent', '#ff6a00')};
    color: {c.get('button_text', '#ffffff')};
    border: none;
    border-radius: {r.get('small', 4)}px;
    padding: 7px 16px;
    font-size: {f.get('size_normal', 12)}px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {c.get('accent_hover', '#ff8533')};
}}

QPushButton:pressed {{
    background-color: {c.get('accent_pressed', '#cc5500')};
}}

QPushButton:disabled {{
    background-color: {c.get('surface_overlay', '#252525')};
    color: {c.get('text_muted', '#555555')};
}}

QDateEdit {{
    background-color: {c.get('input_bg', '#1a1a1a')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('input_border', '#333333')};
    border-radius: {r.get('small', 4)}px;
    padding: 5px 10px;
    font-size: {f.get('size_normal', 12)}px;
}}

QDateEdit:focus {{
    border: 1px solid {c.get('input_focus', '#ff6a00')};
}}

QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

QCalendarWidget {{
    background-color: {c.get('surface', '#161616')};
    color: {c.get('text_primary', '#f0f0f0')};
}}

QStatusBar {{
    background-color: {c.get('surface', '#161616')};
    color: {c.get('text_secondary', '#999999')};
    border-top: 1px solid {c.get('border', '#2a2a2a')};
    font-size: {f.get('size_small', 10)}px;
}}

QToolTip {{
    background-color: {c.get('surface_overlay', '#252525')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('border_accent', '#ff6a00')};
    border-radius: {r.get('small', 4)}px;
    padding: 4px 8px;
    font-size: {f.get('size_small', 10)}px;
}}

QLabel {{
    background-color: transparent;
    color: {c.get('text_primary', '#f0f0f0')};
    border: none;
}}

QFrame {{
    background-color: transparent;
}}

QSpinBox {{
    background-color: {c.get('input_bg', '#1a1a1a')};
    color: {c.get('text_primary', '#f0f0f0')};
    border: 1px solid {c.get('input_border', '#333333')};
    border-radius: {r.get('small', 4)}px;
    padding: 5px 8px;
}}

QSpinBox:focus {{
    border: 1px solid {c.get('input_focus', '#ff6a00')};
}}

QCheckBox {{
    color: {c.get('text_primary', '#f0f0f0')};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {c.get('input_border', '#333333')};
    border-radius: 3px;
    background-color: {c.get('input_bg', '#1a1a1a')};
}}

QCheckBox::indicator:checked {{
    background-color: {c.get('accent', '#ff6a00')};
    border: 1px solid {c.get('accent', '#ff6a00')};
    image: url("{str(Path(__file__).parent / 'assets' / 'check.svg').replace(chr(92), '/')}");
}}

QCheckBox::indicator:indeterminate {{
    background-color: {c.get('accent_dim', '#4d2000')};
    border: 1px solid {c.get('accent', '#ff6a00')};
}}

QGroupBox {{
    border: 1px solid {c.get('border', '#2a2a2a')};
    border-radius: {r.get('medium', 8)}px;
    margin-top: 12px;
    padding-top: 8px;
    color: {c.get('text_secondary', '#999999')};
    font-size: {f.get('size_normal', 12)}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {c.get('accent', '#ff6a00')};
    left: 12px;
}}
"""
