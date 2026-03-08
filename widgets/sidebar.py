from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta
import helper.theme_system as theme


MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

MONTH_ICONS = [
    "fa5s.snowflake", "fa5s.heart", "fa5s.leaf", "fa5s.seedling",
    "fa5s.sun", "fa5s.umbrella-beach", "fa5s.fire", "fa5s.campground",
    "fa5s.apple-alt", "fa5s.ghost", "fa5s.cloud-sun", "fa5s.holly-berry"
]


class MonthItem(QFrame):
    clicked = Signal(int)

    def __init__(self, month_idx: int, parent=None):
        # month_idx: -1 = All Year, 0-11 = Jan-Dec
        super().__init__(parent)
        self.month_idx = month_idx
        self._selected = False
        self._setup_ui()
        self._apply_style(False)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(10)

        icon_label = QLabel()
        if self.month_idx == -1:
            try:
                icon = qta.icon("fa5s.calendar-alt", color=theme.color("text_secondary"))
                icon_label.setPixmap(icon.pixmap(16, 16))
            except Exception:
                icon_label.setText("")
        else:
            try:
                icon = qta.icon(MONTH_ICONS[self.month_idx], color=theme.color("text_secondary"))
                icon_label.setPixmap(icon.pixmap(16, 16))
            except Exception:
                icon_label.setText("")
        icon_label.setFixedSize(18, 18)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label = icon_label

        label_text = "All Year" if self.month_idx == -1 else MONTHS[self.month_idx]
        self._label = QLabel(label_text)
        self._label.setFont(QFont(theme.font_family(), theme.font_size("size_normal")))

        layout.addWidget(icon_label)
        layout.addWidget(self._label)
        layout.addStretch()

        self._count_label = QLabel("")
        self._count_label.setFixedWidth(28)
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font = QFont(theme.font_family(), theme.font_size("size_small"))
        self._count_label.setFont(font)
        self._count_label.setStyleSheet(f"color: {theme.color('text_muted')}; background: transparent;")
        layout.addWidget(self._count_label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_count(self, count: int):
        self._count_label.setText(str(count) if count > 0 else "")

    def _icon_name(self) -> str:
        if self.month_idx == -1:
            return "fa5s.calendar-alt"
        return MONTH_ICONS[self.month_idx]

    def _apply_style(self, selected: bool):
        r = theme.radius("small")
        if selected:
            self.setStyleSheet(f"""
                MonthItem {{
                    background-color: {theme.color('sidebar_item_active')};
                    border: 1px solid {theme.color('accent')};
                    border-radius: {r}px;
                }}
            """)
            self._label.setStyleSheet(f"color: {theme.color('accent')}; font-weight: bold; background: transparent;")
            try:
                icon = qta.icon(self._icon_name(), color=theme.color("accent"))
                self._icon_label.setPixmap(icon.pixmap(16, 16))
            except Exception:
                pass
        else:
            self.setStyleSheet(f"""
                MonthItem {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: {r}px;
                }}
                MonthItem:hover {{
                    background-color: {theme.color('sidebar_item_hover')};
                    border: 1px solid {theme.color('border')};
                }}
            """)
            self._label.setStyleSheet(f"color: {theme.color('text_primary')}; background: transparent;")
            try:
                icon = qta.icon(self._icon_name(), color=theme.color("text_secondary"))
                self._icon_label.setPixmap(icon.pixmap(16, 16))
            except Exception:
                pass

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.month_idx)
        super().mousePressEvent(event)


class Sidebar(QWidget):
    month_selected = Signal(int)   # 0 = All Year, 1-12 = month
    year_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_year = 2026
        self._current_month = 0
        self._month_items = []
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sidebar_root")
        self.setStyleSheet(f"QWidget#sidebar_root {{ background-color: {theme.color('sidebar_bg')}; }}")
        self.setMinimumWidth(160)
        self.setMaximumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        year_frame = QFrame()
        year_frame.setObjectName("year_frame")
        year_frame.setStyleSheet(f"""
            QFrame#year_frame {{
                background-color: {theme.color('surface_raised')};
                border: 1px solid {theme.color('border_accent')};
                border-radius: {theme.radius('medium')}px;
            }}
        """)
        year_layout = QHBoxLayout(year_frame)
        year_layout.setContentsMargins(8, 6, 8, 6)
        year_layout.setSpacing(6)

        self._prev_btn = QPushButton()
        self._prev_btn.setFixedSize(28, 28)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('surface_overlay')};
                border: 1px solid {theme.color('border')};
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_dim')};
                border: 1px solid {theme.color('accent')};
            }}
        """)
        try:
            self._prev_btn.setIcon(qta.icon("fa5s.chevron-left", color=theme.color("text_primary")))
        except Exception:
            self._prev_btn.setText("<")
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._prev_year)

        self._year_label = QLabel(str(self._current_year))
        self._year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(theme.font_family(), theme.font_size("size_xlarge"))
        font.setBold(True)
        self._year_label.setFont(font)
        self._year_label.setStyleSheet(f"color: {theme.color('accent')}; background: transparent;")

        self._next_btn = QPushButton()
        self._next_btn.setFixedSize(28, 28)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.color('surface_overlay')};
                border: 1px solid {theme.color('border')};
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {theme.color('accent_dim')};
                border: 1px solid {theme.color('accent')};
            }}
        """)
        try:
            self._next_btn.setIcon(qta.icon("fa5s.chevron-right", color=theme.color("text_primary")))
        except Exception:
            self._next_btn.setText(">")
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._next_year)

        year_layout.addWidget(self._prev_btn)
        year_layout.addWidget(self._year_label, 1)
        year_layout.addWidget(self._next_btn)

        layout.addWidget(year_frame)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {theme.color('border')}; max-height: 1px; border: none;")
        layout.addWidget(divider)

        months_label = QLabel("MONTHS")
        months_label.setStyleSheet(f"""
            color: {theme.color('text_muted')};
            font-size: {theme.font_size('size_small')}px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 4px 6px 2px 6px;
            background: transparent;
        """)
        layout.addWidget(months_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        months_container = QWidget()
        months_container.setStyleSheet("background: transparent;")
        months_layout = QVBoxLayout(months_container)
        months_layout.setContentsMargins(0, 0, 0, 0)
        months_layout.setSpacing(2)

        # "All Year" item (month_idx = -1)
        all_item = MonthItem(-1)
        all_item.clicked.connect(self._on_month_clicked)
        self._month_items.append(all_item)
        months_layout.addWidget(all_item)

        for i in range(12):
            item = MonthItem(i)
            item.clicked.connect(self._on_month_clicked)
            self._month_items.append(item)
            months_layout.addWidget(item)

        months_layout.addStretch()
        scroll.setWidget(months_container)
        layout.addWidget(scroll, 1)

        bottom_frame = QFrame()
        bottom_frame.setObjectName("bottom_frame")
        bottom_frame.setStyleSheet(f"""
            QFrame#bottom_frame {{
                background-color: {theme.color('surface')};
                border: 1px solid {theme.color('border')};
                border-radius: {theme.radius('small')}px;
            }}
        """)
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(8, 6, 8, 6)
        bottom_layout.setSpacing(2)

        cal_icon_label = QLabel()
        cal_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cal_icon_label.setStyleSheet("background: transparent; border: none;")
        try:
            cal_icon = qta.icon("fa5s.calendar-alt", color=theme.color("accent"))
            cal_icon_label.setPixmap(cal_icon.pixmap(22, 22))
        except Exception:
            pass

        app_name = QLabel("Holiday Explorer")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet(f"""
            color: {theme.color('text_secondary')};
            font-size: {theme.font_size('size_small')}px;
            background: transparent;
        """)

        bottom_layout.addWidget(cal_icon_label)
        bottom_layout.addWidget(app_name)
        layout.addWidget(bottom_frame)

    def _prev_year(self):
        self._current_year -= 1
        self._year_label.setText(str(self._current_year))
        self.year_changed.emit(self._current_year)

    def _next_year(self):
        self._current_year += 1
        self._year_label.setText(str(self._current_year))
        self.year_changed.emit(self._current_year)

    def _on_month_clicked(self, month_idx: int):
        # month_idx: -1 = All Year, 0-11 = Jan-Dec
        self._select_item(month_idx)
        signal_val = 0 if month_idx == -1 else month_idx + 1
        self.month_selected.emit(signal_val)

    def _select_item(self, month_idx: int):
        for item in self._month_items:
            item.set_selected(item.month_idx == month_idx)
        self._current_month = month_idx

    def set_selected_month(self, month_idx: int):
        """month_idx: -1 = All Year, 0-11 = Jan-Dec"""
        self._select_item(month_idx)

    def set_month_counts(self, counts: dict):
        """counts: {1: n, 2: n, ..., 12: n} — holiday count per month.
        Also sets count for All Year item as total."""
        total = sum(counts.values())
        for item in self._month_items:
            if item.month_idx == -1:
                item.set_count(total)
            else:
                item.set_count(counts.get(item.month_idx + 1, 0))

    def set_year(self, year: int):
        self._current_year = year
        self._year_label.setText(str(year))

    def get_year(self) -> int:
        return self._current_year
