import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QStackedWidget,
    QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import qtawesome as qta
import theme_system as theme


def _date_color(date_str: str) -> str:
    palette = [
        "#ff6a00", "#ff3d71", "#00d4ff", "#00e096",
        "#ffaa00", "#c56cff", "#ff6cb6", "#61f4de",
        "#ffd166", "#06d6a0", "#ef476f", "#118ab2",
    ]
    h = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    return palette[h % len(palette)]


class HolidayCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, holiday: dict, color: str, parent=None):
        super().__init__(parent)
        self._holiday = holiday
        self._color = color
        self._active = False
        self._setup_ui()
        self._apply_style()

    def _apply_style(self):
        r = theme.radius("medium")
        if self._active:
            self.setStyleSheet(f"""
                HolidayCard {{
                    background-color: {theme.color('row_hover')};
                    border-left: 3px solid {self._color};
                    border-top: 1px solid {self._color};
                    border-right: 1px solid {self._color};
                    border-bottom: 1px solid {self._color};
                    border-radius: {r}px;
                }}
                HolidayCard:hover {{
                    background-color: {theme.color('row_hover')};
                    border-left: 3px solid {self._color};
                    border-top: 1px solid {self._color};
                    border-right: 1px solid {self._color};
                    border-bottom: 1px solid {self._color};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                HolidayCard {{
                    background-color: {theme.color('surface_raised')};
                    border: 1px solid {theme.color('border')};
                    border-left: 3px solid {self._color};
                    border-radius: {r}px;
                }}
                HolidayCard:hover {{
                    background-color: {theme.color('row_hover')};
                    border-left: 3px solid {self._color};
                    border-top: 1px solid {self._color};
                    border-right: 1px solid {self._color};
                    border-bottom: 1px solid {self._color};
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        color_dot = QFrame()
        color_dot.setFixedSize(10, 10)
        color_dot.setStyleSheet(f"""
            QFrame {{
                background-color: {self._color};
                border-radius: 5px;
                border: none;
            }}
        """)
        layout.addWidget(color_dot)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(3)

        name_font = QFont(theme.font_family(), theme.font_size("size_medium"))
        name_font.setBold(True)
        name_label = QLabel(self._holiday.get("name", ""))
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {theme.color('text_primary')}; background: transparent;")
        name_label.setWordWrap(True)

        desc = self._holiday.get("description", "")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"color: {theme.color('text_secondary')}; font-size: {theme.font_size('size_small')}px; background: transparent;")
            desc_label.setWordWrap(True)
        else:
            desc_label = None

        info_layout.addWidget(name_label)
        if desc_label:
            info_layout.addWidget(desc_label)

        layout.addLayout(info_layout, 1)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        date_label = QLabel(self._holiday.get("date", ""))
        date_label.setStyleSheet(f"""
            color: {self._color};
            font-size: {theme.font_size('size_small')}px;
            font-weight: bold;
            background: transparent;
        """)
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        types = self._holiday.get("type", [])
        if isinstance(types, list) and types:
            type_text = types[0] if isinstance(types[0], str) else str(types[0])
        else:
            type_text = self._holiday.get("primary_type", "")

        scope = "National" if self._holiday.get("is_national") else self._holiday.get("states", "")
        if isinstance(scope, list):
            scope = ""
        display_type = self._holiday.get("primary_type", "") or type_text
        type_label = QLabel(display_type)
        type_label.setStyleSheet(f"""
            color: {theme.color('text_muted')};
            font-size: {theme.font_size('size_small') - 1}px;
            background: {theme.color('tag_bg')};
            border-radius: {theme.radius('small')}px;
            padding: 1px 6px;
        """)
        type_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        right_layout.addWidget(date_label)
        right_layout.addWidget(type_label)
        layout.addLayout(right_layout)

        from PySide6.QtWidgets import QPushButton
        copy_btn = QPushButton()
        copy_btn.setFixedSize(22, 22)
        copy_btn.setToolTip("Copy holiday name")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {theme.radius('small')}px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('surface_overlay')};
            }}
        """)
        try:
            copy_btn.setIcon(qta.icon("fa5s.copy", color=theme.color("text_muted")))
        except Exception:
            copy_btn.setText("\u29c9")
        _name = self._holiday.get("name", "")
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QToolTip
        def _copy_action():
            QApplication.clipboard().setText(_name)
            # show a brief tooltip near the button
            pos = copy_btn.mapToGlobal(QPoint(copy_btn.width()//2, -5))
            QToolTip.showText(pos, "Copied: " + _name, copy_btn)
        copy_btn.clicked.connect(_copy_action)
        layout.addWidget(copy_btn)

        arrow_label = QLabel()
        try:
            arrow_label.setPixmap(qta.icon("fa5s.chevron-right", color=theme.color("text_muted")).pixmap(12, 12))
        except Exception:
            arrow_label.setText(">")
        arrow_label.setStyleSheet("background: transparent;")
        layout.addWidget(arrow_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._holiday)
        super().mousePressEvent(event)


class DateGroupHeader(QFrame):
    def __init__(self, date_str: str, color: str, count: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        bar = QFrame()
        bar.setFixedSize(4, 20)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
        layout.addWidget(bar)

        date_label = QLabel(date_str)
        font = QFont(theme.font_family(), theme.font_size("size_normal"))
        font.setBold(True)
        date_label.setFont(font)
        date_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(date_label)

        badge = QLabel(f"{count} holiday{'s' if count > 1 else ''}")
        badge.setStyleSheet(f"""
            color: {theme.color('text_muted')};
            background-color: {theme.color('tag_bg')};
            border-radius: {theme.radius('pill')}px;
            padding: 1px 8px;
            font-size: {theme.font_size('size_small')}px;
        """)
        layout.addWidget(badge)
        layout.addStretch()

        self.setStyleSheet("background: transparent;")


class EmptyState(QWidget):
    def __init__(self, message="No holidays found", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            icon = qta.icon("fa5s.calendar-times", color=theme.color("text_muted"))
            icon_label.setPixmap(icon.pixmap(48, 48))
        except Exception:
            pass

        text_label = QLabel(message)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"color: {theme.color('text_muted')}; font-size: {theme.font_size('size_large')}px; background: transparent;")

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        self.setStyleSheet("background: transparent;")


class HolidayList(QWidget):
    holiday_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._holidays = []
        self._filtered = []
        self._search_text = ""
        self._active_card = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"background: transparent; border: none;")

        self._content = QWidget()
        self._content.setStyleSheet(f"background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(6)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)

        self._empty_state = EmptyState("Select a month to load holidays")

        self._stack.addWidget(self._scroll)
        self._stack.addWidget(self._empty_state)
        self._stack.setCurrentWidget(self._empty_state)

        layout.addWidget(self._stack)

    def set_holidays(self, holidays: list):
        self._holidays = holidays
        self._apply_filter()

    def set_search(self, text: str):
        self._search_text = text.lower()
        self._apply_filter()

    def _apply_filter(self):
        if self._search_text:
            self._filtered = [
                h for h in self._holidays
                if self._search_text in h.get("name", "").lower()
                or self._search_text in h.get("description", "").lower()
            ]
        else:
            self._filtered = list(self._holidays)
        self._render()

    def _render(self):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._filtered:
            msg = "No holidays match your search" if self._search_text else "No holidays found for this month"
            self._empty_state = EmptyState(msg)
            self._stack.removeWidget(self._stack.widget(1))
            self._stack.addWidget(self._empty_state)
            self._stack.setCurrentIndex(1)
            return

        self._stack.setCurrentIndex(0)

        grouped = {}
        for h in self._filtered:
            date = h.get("date", "unknown")
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(h)

        insert_pos = 0
        for date_str in sorted(grouped.keys()):
            holidays_for_date = grouped[date_str]
            color = _date_color(date_str)

            header = DateGroupHeader(date_str, color, len(holidays_for_date))
            self._content_layout.insertWidget(insert_pos, header)
            insert_pos += 1

            for holiday in holidays_for_date:
                card = HolidayCard(holiday, color)
                card.clicked.connect(self._on_card_clicked)
                self._content_layout.insertWidget(insert_pos, card)
                insert_pos += 1

    def _on_card_clicked(self, holiday: dict):
        # Deactivate previously active card
        if self._active_card is not None:
            try:
                self._active_card.set_active(False)
            except RuntimeError:
                pass
        # Find the card that was clicked and activate it
        sender = self.sender()
        if isinstance(sender, HolidayCard):
            sender.set_active(True)
            self._active_card = sender
        self.holiday_selected.emit(holiday)

    def clear(self):
        self._holidays = []
        self._filtered = []
        self._render()
        self._stack.setCurrentIndex(1)

    def show_loading(self):
        self._empty_state = EmptyState("Loading holidays...")
        self._stack.removeWidget(self._stack.widget(1))
        self._stack.addWidget(self._empty_state)
        self._stack.setCurrentIndex(1)

    def show_error(self, message: str):
        self._empty_state = EmptyState(f"Error: {message}")
        self._stack.removeWidget(self._stack.widget(1))
        self._stack.addWidget(self._empty_state)
        self._stack.setCurrentIndex(1)
