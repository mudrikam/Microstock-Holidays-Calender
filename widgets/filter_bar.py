from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta
import helper.theme_system as theme


class FilterBar(QWidget):
    country_changed = Signal(str)
    search_changed = Signal(str)
    view_mode_changed = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._countries = []
        self._current_mode = "list"
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.color('surface')};
            }}
        """)
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        country_icon = QLabel()
        try:
            country_icon.setPixmap(qta.icon("fa5s.globe", color=theme.color("text_secondary")).pixmap(16, 16))
        except Exception:
            pass
        country_icon.setFixedSize(20, 20)
        layout.addWidget(country_icon)

        self._country_combo = QComboBox()
        self._country_combo.setMinimumWidth(160)
        self._country_combo.setMaximumWidth(220)
        self._country_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._country_combo.currentIndexChanged.connect(self._on_country_changed)
        layout.addWidget(self._country_combo)

        sep2 = QLabel("|")
        sep2.setStyleSheet(f"color: {theme.color('border')}; background: transparent;")
        layout.addWidget(sep2)

        search_icon = QLabel()
        try:
            search_icon.setPixmap(qta.icon("fa5s.search", color=theme.color("text_secondary")).pixmap(16, 16))
        except Exception:
            pass
        search_icon.setFixedSize(20, 20)
        layout.addWidget(search_icon)

        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Search holidays...")
        self._search_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._search_field.textChanged.connect(self._on_search_changed)
        self._search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.color('input_bg')};
                color: {theme.color('text_primary')};
                border: 1px solid {theme.color('input_border')};
                border-radius: {theme.radius('small')}px;
                padding: 5px 10px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme.color('accent')};
            }}
        """)
        layout.addWidget(self._search_field, 1)

        self._clear_btn = QPushButton()
        self._clear_btn.setFixedSize(32, 32)
        self._clear_btn.setToolTip("Clear search")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('surface_overlay')};
                border: 1px solid {theme.color('border')};
                border-radius: {theme.radius('small')}px;
            }}
            QPushButton:hover {{
                border: 1px solid {theme.color('accent')};
                background-color: {theme.color('accent_dim')};
            }}
        """)
        try:
            self._clear_btn.setIcon(qta.icon("fa5s.times", color=theme.color("text_secondary")))
        except Exception:
            self._clear_btn.setText("X")
        self._clear_btn.clicked.connect(lambda: self._search_field.clear())
        layout.addWidget(self._clear_btn)

        sep3 = QLabel("|")
        sep3.setStyleSheet(f"color: {theme.color('border')}; background: transparent;")
        layout.addWidget(sep3)

        self._list_btn = QPushButton()
        self._list_btn.setFixedSize(32, 32)
        self._list_btn.setToolTip("List view")
        self._list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            self._list_btn.setIcon(qta.icon("fa5s.list", color=theme.color("accent")))
        except Exception:
            self._list_btn.setText("L")
        self._list_btn.clicked.connect(lambda: self._set_mode("list"))

        self._cal_btn = QPushButton()
        self._cal_btn.setFixedSize(32, 32)
        self._cal_btn.setToolTip("Calendar view")
        self._cal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            self._cal_btn.setIcon(qta.icon("fa5s.calendar-alt", color=theme.color("text_secondary")))
        except Exception:
            self._cal_btn.setText("C")
        self._cal_btn.clicked.connect(lambda: self._set_mode("calendar"))

        for btn in [self._list_btn, self._cal_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.color('surface_overlay')};
                    border: 1px solid {theme.color('border')};
                    border-radius: {theme.radius('small')}px;
                }}
                QPushButton:hover {{
                    border: 1px solid {theme.color('accent')};
                }}
            """)

        layout.addWidget(self._list_btn)
        layout.addWidget(self._cal_btn)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setFixedSize(32, 32)
        self._refresh_btn.setToolTip("Refresh / Force reload from API")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('accent')};
                border: none;
                border-radius: {theme.radius('small')}px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_hover')};
            }}
        """)
        try:
            self._refresh_btn.setIcon(qta.icon("fa5s.sync-alt", color="#ffffff"))
        except Exception:
            self._refresh_btn.setText("R")
        self._refresh_btn.clicked.connect(self.refresh_requested)
        layout.addWidget(self._refresh_btn)

        self._update_mode_buttons()

    def _set_mode(self, mode: str):
        self._current_mode = mode
        self._update_mode_buttons()
        self.view_mode_changed.emit(mode)

    def _update_mode_buttons(self):
        if self._current_mode == "list":
            self._list_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.color('accent_dim')};
                    border: 1px solid {theme.color('accent')};
                    border-radius: {theme.radius('small')}px;
                }}
            """)
            try:
                self._list_btn.setIcon(qta.icon("fa5s.list", color=theme.color("accent")))
                self._cal_btn.setIcon(qta.icon("fa5s.calendar-alt", color=theme.color("text_secondary")))
            except Exception:
                pass
            self._cal_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.color('surface_overlay')};
                    border: 1px solid {theme.color('border')};
                    border-radius: {theme.radius('small')}px;
                }}
                QPushButton:hover {{
                    border: 1px solid {theme.color('accent')};
                }}
            """)
        else:
            self._cal_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.color('accent_dim')};
                    border: 1px solid {theme.color('accent')};
                    border-radius: {theme.radius('small')}px;
                }}
            """)
            try:
                self._cal_btn.setIcon(qta.icon("fa5s.calendar-alt", color=theme.color("accent")))
                self._list_btn.setIcon(qta.icon("fa5s.list", color=theme.color("text_secondary")))
            except Exception:
                pass
            self._list_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.color('surface_overlay')};
                    border: 1px solid {theme.color('border')};
                    border-radius: {theme.radius('small')}px;
                }}
                QPushButton:hover {{
                    border: 1px solid {theme.color('accent')};
                }}
            """)

    def _on_country_changed(self, index: int):
        code = self._country_combo.itemData(index)
        if code:
            self.country_changed.emit(code)

    def _on_search_changed(self, text: str):
        self.search_changed.emit(text)

    def populate_countries(self, countries: list):
        self._country_combo.blockSignals(True)
        self._country_combo.clear()
        self._country_combo.addItem("🌍  World (All Countries)", "WORLD")
        for c in countries:
            self._country_combo.addItem(f"{c['code']} - {c['name']}", c["code"])
        self._country_combo.blockSignals(False)

    def set_country(self, code: str):
        self._country_combo.blockSignals(True)
        for i in range(self._country_combo.count()):
            if self._country_combo.itemData(i) == code.upper():
                self._country_combo.setCurrentIndex(i)
                break
        self._country_combo.blockSignals(False)

    def get_country(self) -> str:
        idx = self._country_combo.currentIndex()
        if idx >= 0:
            return self._country_combo.itemData(idx) or ""
        return ""

    def get_search_text(self) -> str:
        return self._search_field.text()

    def get_view_mode(self) -> str:
        return self._current_mode

    def set_view_mode(self, mode: str):
        self._current_mode = mode
        self._update_mode_buttons()
