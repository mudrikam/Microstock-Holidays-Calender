import calendar
import hashlib
from datetime import date as Date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta
import helper.theme_system as theme


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _date_color(date_str: str) -> str:
    palette = [
        "#ff6a00", "#ff3d71", "#00d4ff", "#00e096",
        "#ffaa00", "#c56cff", "#ff6cb6", "#61f4de",
        "#ffd166", "#06d6a0", "#ef476f", "#118ab2",
    ]
    h = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    return palette[h % len(palette)]


class CalendarCell(QFrame):
    clicked = Signal(str, list)

    def __init__(self, day: int, date_str: str, holidays: list, is_today: bool = False, parent=None):
        super().__init__(parent)
        self._day = day
        self._date_str = date_str
        self._holidays = holidays
        self._is_today = is_today
        self._setup_ui()

    def _setup_ui(self):
        r = theme.radius("small")
        has_holidays = bool(self._holidays)
        if self._is_today:
            bg = theme.color("calendar_today")
            border = theme.color("accent")
        elif has_holidays:
            bg = theme.color("calendar_cell_holiday")
            border = theme.color("border")
        else:
            bg = theme.color("calendar_cell")
            border = theme.color("border")

        self.setStyleSheet(f"""
            CalendarCell {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {r}px;
            }}
            CalendarCell:hover {{
                border: 1px solid {theme.color('accent')};
                background-color: {theme.color('row_hover')};
            }}
        """)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if self._holidays:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(3)

        day_font = QFont(theme.font_family(), theme.font_size("size_medium"))
        if self._is_today:
            day_font.setBold(True)

        day_label = QLabel(str(self._day))
        day_label.setFont(day_font)
        if self._is_today:
            day_label.setStyleSheet(f"""
                color: {theme.color('accent')};
                background-color: {theme.color('accent')};
                color: white;
                border-radius: {theme.radius('pill')}px;
                padding: 1px 5px;
                font-weight: bold;
            """)
            day_label.setFixedWidth(26)
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            day_label.setStyleSheet(f"color: {theme.color('text_secondary')}; background: transparent;")
        layout.addWidget(day_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        for h in self._holidays[:3]:
            date_str = h.get("date", "")
            color = _date_color(date_str)
            name = h.get("name", "")
            chip = QLabel(name[:16] + ("..." if len(name) > 16 else ""))
            chip.setStyleSheet(f"""
                color: {color};
                background-color: {color}22;
                border: 1px solid {color}55;
                border-radius: 3px;
                padding: 0px 4px;
                font-size: {theme.font_size('size_small') - 1}px;
            """)
            chip.setWordWrap(False)
            layout.addWidget(chip)

        if len(self._holidays) > 3:
            more_label = QLabel(f"+{len(self._holidays) - 3} more")
            more_label.setStyleSheet(f"""
                color: {theme.color('text_muted')};
                font-size: {theme.font_size('size_small') - 1}px;
                background: transparent;
            """)
            layout.addWidget(more_label)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._holidays:
            self.clicked.emit(self._date_str, self._holidays)
        super().mousePressEvent(event)


class EmptyCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.color('background')};
                border: 1px solid {theme.color('border')}22;
                border-radius: {theme.radius('small')}px;
            }}
        """)


class CalendarView(QWidget):
    date_clicked = Signal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._year = 2026
        self._month = 1
        self._holidays = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.color('calendar_header')};
                border: none;
                border-radius: {theme.radius('small')}px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 6, 16, 6)

        self._month_year_label = QLabel()
        font = QFont(theme.font_family(), theme.font_size("size_large"))
        font.setBold(True)
        self._month_year_label.setFont(font)
        self._month_year_label.setStyleSheet(f"color: {theme.color('accent')}; background: transparent;")
        header_layout.addWidget(self._month_year_label)
        header_layout.addStretch()

        count_label_holder = QHBoxLayout()
        self._count_label = QLabel()
        self._count_label.setStyleSheet(f"""
            color: {theme.color('text_secondary')};
            background-color: {theme.color('tag_bg')};
            border-radius: {theme.radius('pill')}px;
            padding: 2px 10px;
            font-size: {theme.font_size('size_small')}px;
        """)
        header_layout.addWidget(self._count_label)

        layout.addWidget(header_frame)

        weekday_frame = QFrame()
        weekday_frame.setStyleSheet("background: transparent;")
        weekday_layout = QHBoxLayout(weekday_frame)
        weekday_layout.setContentsMargins(0, 0, 0, 0)
        weekday_layout.setSpacing(4)
        for wd in WEEKDAYS:
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"""
                color: {'#ff6a00' if wd in ('Sat', 'Sun') else theme.color('text_muted')};
                font-size: {theme.font_size('size_small')}px;
                font-weight: bold;
                background: transparent;
                padding: 2px 0;
            """)
            weekday_layout.addWidget(lbl, 1)
        layout.addWidget(weekday_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(4)

        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll, 1)

    def set_month(self, year: int, month: int):
        self._year = year
        self._month = month
        self._render()

    def set_holidays(self, holidays: list):
        self._holidays = holidays
        self._render()

    def _render(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        import calendar as cal_module
        month_name = cal_module.month_name[self._month]
        self._month_year_label.setText(f"{month_name} {self._year}")
        self._count_label.setText(f"{len(self._holidays)} holidays")

        today = Date.today()

        date_holiday_map = {}
        for h in self._holidays:
            date_str = h.get("date", "")
            if date_str:
                if date_str not in date_holiday_map:
                    date_holiday_map[date_str] = []
                date_holiday_map[date_str].append(h)

        first_weekday, num_days = calendar.monthrange(self._year, self._month)

        row = 0
        col = first_weekday

        for day in range(1, num_days + 1):
            date_obj = Date(self._year, self._month, day)
            date_str = date_obj.isoformat()
            holidays_on_day = date_holiday_map.get(date_str, [])
            is_today = (date_obj == today)

            cell = CalendarCell(day, date_str, holidays_on_day, is_today)
            cell.clicked.connect(self.date_clicked)
            self._grid.addWidget(cell, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1

        if col > 0:
            for c in range(col, 7):
                self._grid.addWidget(EmptyCell(), row, c)

        for c in range(7):
            self._grid.setColumnStretch(c, 1)

    def clear(self):
        self._holidays = []
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._month_year_label.setText("")
        self._count_label.setText("")
