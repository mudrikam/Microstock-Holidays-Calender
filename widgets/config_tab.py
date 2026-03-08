from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QGroupBox,
    QSpinBox, QCheckBox, QComboBox, QScrollArea,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta
import helper.theme_system as theme
from configs import config_manager
from helper import cache_manager
from helper.logger import logger


class FieldRow(QFrame):
    def __init__(self, label: str, widget, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        lbl = QLabel(label)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet(f"color: {theme.color('text_secondary')}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(lbl)
        layout.addWidget(widget, 1)


class ConfigTab(QWidget):
    config_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        page_title = QLabel("Configuration")
        font = QFont(theme.font_family(), theme.font_size("size_title"))
        font.setBold(True)
        page_title.setFont(font)
        page_title.setStyleSheet(f"color: {theme.color('accent')}; background: transparent;")
        layout.addWidget(page_title)

        subtitle = QLabel("Manage API settings, cache options, and UI preferences.")
        subtitle.setStyleSheet(f"color: {theme.color('text_muted')}; background: transparent; font-size: {theme.font_size('size_normal')}px;")
        layout.addWidget(subtitle)

        api_group = QGroupBox("API Settings")
        api_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {theme.color('border')};
                border-radius: {theme.radius('medium')}px;
                margin-top: 14px;
                padding-top: 10px;
                color: {theme.color('text_secondary')};
                background-color: {theme.color('surface')};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {theme.color('accent')};
                left: 12px;
                font-weight: bold;
            }}
        """)
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(10)
        api_layout.setContentsMargins(16, 16, 16, 16)

        self._api_key_field = QLineEdit()
        self._api_key_field.setPlaceholderText("Enter your Calendarific API key...")
        self._api_key_field.setEchoMode(QLineEdit.EchoMode.Password)

        key_row_layout = QHBoxLayout()
        key_row_layout.setSpacing(6)
        key_row_layout.addWidget(self._api_key_field, 1)

        toggle_visibility_btn = QPushButton()
        toggle_visibility_btn.setFixedSize(32, 32)
        toggle_visibility_btn.setCheckable(True)
        toggle_visibility_btn.setToolTip("Show/hide API key")
        toggle_visibility_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_visibility_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('surface_overlay')};
                border: 1px solid {theme.color('border')};
                border-radius: {theme.radius('small')}px;
            }}
            QPushButton:checked {{
                background-color: {theme.color('accent_dim')};
                border: 1px solid {theme.color('accent')};
            }}
            QPushButton:hover {{
                border: 1px solid {theme.color('accent')};
            }}
        """)
        try:
            toggle_visibility_btn.setIcon(qta.icon("fa5s.eye", color=theme.color("text_secondary")))
        except Exception:
            toggle_visibility_btn.setText("V")

        def toggle_key_visibility(checked):
            if checked:
                self._api_key_field.setEchoMode(QLineEdit.EchoMode.Normal)
                try:
                    toggle_visibility_btn.setIcon(qta.icon("fa5s.eye-slash", color=theme.color("accent")))
                except Exception:
                    pass
            else:
                self._api_key_field.setEchoMode(QLineEdit.EchoMode.Password)
                try:
                    toggle_visibility_btn.setIcon(qta.icon("fa5s.eye", color=theme.color("text_secondary")))
                except Exception:
                    pass

        toggle_visibility_btn.toggled.connect(toggle_key_visibility)
        key_row_layout.addWidget(toggle_visibility_btn)

        api_layout.addWidget(FieldRow("API Key", self._api_key_field))

        base_url_field_widget = QWidget()
        base_url_field_widget.setStyleSheet("background: transparent;")
        base_url_row = QHBoxLayout(base_url_field_widget)
        base_url_row.setContentsMargins(0, 0, 0, 0)
        base_url_row.setSpacing(0)
        self._base_url_field = QLineEdit()
        self._base_url_field.setPlaceholderText("https://calendarific.com/api/v2")
        base_url_row.addWidget(self._base_url_field)

        api_layout.addWidget(FieldRow("Base URL", self._base_url_field))

        self._default_country_field = QLineEdit()
        self._default_country_field.setPlaceholderText("e.g. US")
        api_layout.addWidget(FieldRow("Default Country", self._default_country_field))

        get_key_btn = QPushButton("Get API Key at calendarific.com")
        get_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        get_key_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.color('accent')};
                border: 1px solid {theme.color('accent')}44;
                border-radius: {theme.radius('small')}px;
                padding: 5px 12px;
                font-size: {theme.font_size('size_small')}px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_dim')};
                border: 1px solid {theme.color('accent')};
            }}
        """)
        try:
            get_key_btn.setIcon(qta.icon("fa5s.external-link-alt", color=theme.color("accent")))
        except Exception:
            pass
        api_layout.addWidget(get_key_btn)
        layout.addWidget(api_group)

        # open browser when user clicks link
        def open_api_page():
            import webbrowser
            webbrowser.open("https://calendarific.com/account/dashboard")
        get_key_btn.clicked.connect(open_api_page)

        cache_group = QGroupBox("Cache Settings")
        cache_group.setStyleSheet(api_group.styleSheet())
        cache_layout = QVBoxLayout(cache_group)
        cache_layout.setSpacing(10)
        cache_layout.setContentsMargins(16, 16, 16, 16)

        self._expire_days_spin = QSpinBox()
        self._expire_days_spin.setRange(1, 365)
        self._expire_days_spin.setValue(7)
        self._expire_days_spin.setSuffix(" days")
        cache_layout.addWidget(FieldRow("Cache Expiry", self._expire_days_spin))

        self._use_sqlite_check = QCheckBox("Use SQLite cache (recommended)")
        self._use_sqlite_check.setStyleSheet(f"color: {theme.color('text_primary')}; background: transparent;")
        cache_layout.addWidget(self._use_sqlite_check)

        self._sqlite_path_field = QLineEdit()
        self._sqlite_path_field.setPlaceholderText("cache.db")
        cache_layout.addWidget(FieldRow("SQLite File", self._sqlite_path_field))

        self._json_fallback_field = QLineEdit()
        self._json_fallback_field.setPlaceholderText("cache_fallback.json")
        cache_layout.addWidget(FieldRow("JSON Fallback", self._json_fallback_field))

        cache_actions = QHBoxLayout()
        cache_actions.setSpacing(8)

        clear_cache_btn = QPushButton("Clear All Cache")
        clear_cache_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_cache_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('surface_overlay')};
                color: {theme.color('error')};
                border: 1px solid {theme.color('error')}44;
                border-radius: {theme.radius('small')}px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: #3a0010;
                border: 1px solid {theme.color('error')};
            }}
        """)
        try:
            clear_cache_btn.setIcon(qta.icon("fa5s.trash", color=theme.color("error")))
        except Exception:
            pass
        clear_cache_btn.clicked.connect(self._clear_cache)

        cache_actions.addWidget(clear_cache_btn)
        cache_actions.addStretch()
        cache_layout.addLayout(cache_actions)
        layout.addWidget(cache_group)

        save_btn = QPushButton("Save Configuration")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('accent')};
                color: white;
                border: none;
                border-radius: {theme.radius('medium')}px;
                font-size: {theme.font_size('size_medium')}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {theme.color('accent_pressed')};
            }}
        """)
        try:
            save_btn.setIcon(qta.icon("fa5s.save", color="white"))
        except Exception:
            pass
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load_values(self):
        self._api_key_field.setText(config_manager.get_api_key())
        self._base_url_field.setText(config_manager.get_base_url())
        self._default_country_field.setText(config_manager.get_default_country())
        self._expire_days_spin.setValue(config_manager.get_cache("expire_days", 7))
        self._use_sqlite_check.setChecked(config_manager.get_cache("use_sqlite", True))
        self._sqlite_path_field.setText(config_manager.get_cache("sqlite_path", "cache.db"))
        self._json_fallback_field.setText(config_manager.get_cache("json_fallback_path", "cache_fallback.json"))

    def _save(self):
        config_manager.set_value("api", "key", self._api_key_field.text().strip())
        config_manager.set_value("api", "base_url", self._base_url_field.text().strip() or "https://calendarific.com/api/v2")
        config_manager.set_value("api", "default_country", self._default_country_field.text().strip().upper() or "US")
        config_manager.set_value("cache", "expire_days", self._expire_days_spin.value())
        config_manager.set_value("cache", "use_sqlite", self._use_sqlite_check.isChecked())
        config_manager.set_value("cache", "sqlite_path", self._sqlite_path_field.text().strip() or "cache.db")
        config_manager.set_value("cache", "json_fallback_path", self._json_fallback_field.text().strip() or "cache_fallback.json")
        config_manager.save()
        logger.success("Configuration saved.")
        self.config_saved.emit()

    def _clear_cache(self):
        reply = QMessageBox.question(
            self, "Clear Cache",
            "This will delete all cached holiday data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            cache_manager.clear_all()
