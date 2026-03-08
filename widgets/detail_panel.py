import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import qtawesome as qta
import helper.theme_system as theme
from helper.search_helper import PLATFORMS, ico_path


class MetaRow(QFrame):
    def __init__(self, icon_name: str, label: str, value: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.color('surface_overlay')};
                border: none;
                border-radius: {theme.radius('small')}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            ic = qta.icon(icon_name, color=color or theme.color("accent"))
            icon_label.setPixmap(ic.pixmap(14, 14))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        key_label = QLabel(label)
        key_label.setStyleSheet(f"color: {theme.color('text_muted')}; font-size: {theme.font_size('size_small')}px; background: transparent;")
        key_label.setFixedWidth(70)
        layout.addWidget(key_label)

        val_label = QLabel(value)
        val_label.setStyleSheet(f"color: {color or theme.color('text_primary')}; font-size: {theme.font_size('size_normal')}px; background: transparent;")
        val_label.setWordWrap(True)
        layout.addWidget(val_label, 1)


class DetailPanel(QWidget):
    close_requested = Signal()
    search_platform_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._holiday = None
        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        self.setObjectName("detail_panel_root")
        self.setMinimumWidth(240)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QWidget#detail_panel_root {{
                background-color: {theme.color('surface')};
                border-left: 1px solid {theme.color('border_accent')};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("detail_header")
        header.setStyleSheet(f"""
            QFrame#detail_header {{
                background-color: {theme.color('surface_raised')};
                border-bottom: 1px solid {theme.color('border_accent')};
                border-left: none;
                border-right: none;
                border-top: none;
            }}
        """)
        header.setFixedHeight(46)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 8, 6)
        header_layout.setSpacing(8)

        detail_icon = QLabel()
        try:
            detail_icon.setPixmap(qta.icon("fa5s.info-circle", color=theme.color("accent")).pixmap(16, 16))
        except Exception:
            pass
        detail_icon.setStyleSheet("background: transparent;")

        title_lbl = QLabel("Holiday Details")
        font = QFont(theme.font_family(), theme.font_size("size_normal"))
        font.setBold(True)
        title_lbl.setFont(font)
        title_lbl.setStyleSheet(f"color: {theme.color('text_primary')}; background: transparent;")

        close_btn = QPushButton()
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Close panel")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {theme.color('border')};
                border-radius: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_dim')};
                border: 1px solid {theme.color('accent')};
            }}
        """)
        try:
            close_btn.setIcon(qta.icon("fa5s.times", color=theme.color("text_secondary")))
        except Exception:
            close_btn.setText("X")
        close_btn.clicked.connect(self._on_close)

        header_layout.addWidget(detail_icon)
        header_layout.addWidget(title_lbl, 1)
        header_layout.addWidget(close_btn)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(10)
        self._content_layout.addStretch()

        scroll.setWidget(self._content_widget)
        outer.addWidget(scroll, 1)

    def _on_close(self):
        self.setVisible(False)
        self.close_requested.emit()

    def show_holiday(self, holiday: dict):
        self._holiday = holiday
        self._render()
        self.setVisible(True)

    def show_date_holidays(self, date_str: str, holidays: list):
        if not holidays:
            return
        if len(holidays) == 1:
            self.show_holiday(holidays[0])
        else:
            self._render_multiple(date_str, holidays)
            self.setVisible(True)

    def _render(self):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._holiday:
            return

        h = self._holiday
        pos = 0

        name_frame = QFrame()
        name_frame.setObjectName("name_frame")
        name_frame.setStyleSheet(f"""
            QFrame#name_frame {{
                background-color: {theme.color('surface_raised')};
                border: 1px solid {theme.color('accent')}55;
                border-radius: {theme.radius('medium')}px;
            }}
        """)
        name_layout = QVBoxLayout(name_frame)
        name_layout.setContentsMargins(12, 10, 12, 10)
        name_layout.setSpacing(4)

        name_label = QLabel(h.get("name", ""))
        font = QFont(theme.font_family(), theme.font_size("size_large"))
        font.setBold(True)
        name_label.setFont(font)
        name_label.setStyleSheet(f"color: {theme.color('accent')}; background: transparent;")
        name_label.setWordWrap(True)
        name_layout.addWidget(name_label)

        date_label = QLabel(h.get("date", ""))
        date_label.setStyleSheet(f"color: {theme.color('text_secondary')}; font-size: {theme.font_size('size_normal')}px; background: transparent;")
        name_layout.addWidget(date_label)
        self._content_layout.insertWidget(pos, name_frame)
        pos += 1

        desc = h.get("description", "")
        if desc:
            desc_frame = QFrame()
            desc_frame.setObjectName("desc_frame")
            desc_frame.setStyleSheet(f"""
                QFrame#desc_frame {{
                    background-color: {theme.color('surface_overlay')};
                    border: none;
                    border-left: 2px solid {theme.color('accent')}44;
                    border-radius: {theme.radius('small')}px;
                }}
            """)
            desc_layout = QVBoxLayout(desc_frame)
            desc_layout.setContentsMargins(10, 8, 10, 8)

            desc_title = QLabel("Description")
            desc_title.setStyleSheet(f"color: {theme.color('text_muted')}; font-size: {theme.font_size('size_small')}px; font-weight: bold; background: transparent;")
            desc_layout.addWidget(desc_title)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"color: {theme.color('text_secondary')}; font-size: {theme.font_size('size_normal')}px; background: transparent;")
            desc_label.setWordWrap(True)
            desc_layout.addWidget(desc_label)
            self._content_layout.insertWidget(pos, desc_frame)
            pos += 1

        types = h.get("type", [])
        if isinstance(types, list):
            type_text = ", ".join(str(t) for t in types) if types else "N/A"
        else:
            type_text = str(types)

        meta_section_label = QLabel("Details")
        meta_section_label.setStyleSheet(f"""
            color: {theme.color('text_muted')};
            font-size: {theme.font_size('size_small')}px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._content_layout.insertWidget(pos, meta_section_label)
        pos += 1

        country_display = h.get("country_name", "") or h.get("country_id", "")
        states_display = h.get("states", "All")
        if isinstance(states_display, list):
            states_display = "All"
        is_national = h.get("is_national", False)
        scope_text = "National" if is_national else states_display

        meta_rows = [
            ("fa5s.calendar-day", "Date", h.get("date", "N/A"), theme.color("text_primary")),
            ("fa5s.globe", "Country", country_display, theme.color("info")),
            ("fa5s.tag", "Type", type_text, theme.color("info")),
            ("fa5s.certificate", "Primary Type", h.get("primary_type", "N/A"), theme.color("accent")),
            ("fa5s.map-marker-alt", "Scope", scope_text, theme.color("success")),
        ]

        for icon_name, label, value, color in meta_rows:
            if value and value != "N/A":
                row = MetaRow(icon_name, label, value, color)
                self._content_layout.insertWidget(pos, row)
                pos += 1

        keyword = h.get("name", "")
        if keyword:
            btn_section_label = QLabel("Search on")
            btn_section_label.setStyleSheet(f"""
                color: {theme.color('text_muted')};
                font-size: {theme.font_size('size_small')}px;
                font-weight: bold;
                letter-spacing: 1px;
                background: transparent;
            """)
            self._content_layout.insertWidget(pos, btn_section_label)
            pos += 1

            btn_container = QWidget()
            btn_container.setStyleSheet("background: transparent;")
            btn_vbox = QVBoxLayout(btn_container)
            btn_vbox.setContentsMargins(0, 0, 0, 0)
            btn_vbox.setSpacing(4)

            for p in PLATFORMS:
                btn = QPushButton(p["name"])
                btn.setFixedHeight(28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip(f"Search '{keyword}' on {p['name']}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme.color('surface_overlay')};
                        color: {theme.color('text_secondary')};
                        border: 1px solid {theme.color('border')};
                        border-radius: 5px;
                        font-size: {theme.font_size('size_small')}px;
                        padding: 0px 6px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.color('accent_dim')};
                        color: {theme.color('text_primary')};
                        border: 1px solid {theme.color('accent')};
                    }}
                """)

                ico_file = ico_path(p["id"])
                if os.path.exists(ico_file):
                    btn.setIcon(QIcon(ico_file))

                pid = p["id"]
                btn.clicked.connect(lambda checked=False, _pid=pid, _kw=keyword:
                    self.search_platform_requested.emit(_pid, _kw))

                btn_vbox.addWidget(btn)

            self._content_layout.insertWidget(pos, btn_container)
            pos += 1

    def _render_multiple(self, date_str: str, holidays: list):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pos = 0

        header_frame = QFrame()
        header_frame.setObjectName("multi_header_frame")
        header_frame.setStyleSheet(f"""
            QFrame#multi_header_frame {{
                background-color: {theme.color('surface_raised')};
                border: 1px solid {theme.color('accent')}55;
                border-radius: {theme.radius('medium')}px;
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)
        date_lbl = QLabel(date_str)
        font = QFont(theme.font_family(), theme.font_size("size_large"))
        font.setBold(True)
        date_lbl.setFont(font)
        date_lbl.setStyleSheet(f"color: {theme.color('accent')}; background: transparent;")
        count_lbl = QLabel(f"{len(holidays)} holiday{'s' if len(holidays) > 1 else ''} on this date")
        count_lbl.setStyleSheet(f"color: {theme.color('text_secondary')}; background: transparent;")
        header_layout.addWidget(date_lbl)
        header_layout.addWidget(count_lbl)
        self._content_layout.insertWidget(pos, header_frame)
        pos += 1

        for h in holidays:
            card = QFrame()
            card.setObjectName("holiday_mini_card")
            card.setStyleSheet(f"""
                QFrame#holiday_mini_card {{
                    background-color: {theme.color('surface_overlay')};
                    border: 1px solid {theme.color('border')};
                    border-radius: {theme.radius('small')}px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(3)

            n = QLabel(h.get("name", ""))
            nf = QFont(theme.font_family(), theme.font_size("size_normal"))
            nf.setBold(True)
            n.setFont(nf)
            n.setStyleSheet(f"color: {theme.color('text_primary')}; background: transparent;")
            n.setWordWrap(True)
            card_layout.addWidget(n)

            desc = h.get("description", "")
            if desc:
                dl = QLabel(desc[:80] + ("..." if len(desc) > 80 else ""))
                dl.setStyleSheet(f"color: {theme.color('text_secondary')}; font-size: {theme.font_size('size_small')}px; background: transparent;")
                dl.setWordWrap(True)
                card_layout.addWidget(dl)

            self._content_layout.insertWidget(pos, card)
            pos += 1
