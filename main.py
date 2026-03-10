import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Windows App User Model ID for proper taskbar icon grouping
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("HolidayExplorer.App.1.0")
    except Exception as e:
        print(f"Failed to set App User Model ID: {e}")

# Suppress benign Qt6/Windows DPI font-size warnings from internal Qt subsystems
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
def _qt_message_handler(msg_type, context, message):
    if msg_type == QtMsgType.QtWarningMsg and "Point size <= 0" in message:
        return  # Qt internal DPI font warning — harmless, suppress
    if msg_type == QtMsgType.QtCriticalMsg or msg_type == QtMsgType.QtFatalMsg:
        sys.stderr.write(f"Qt [{msg_type.name}]: {message}\n")
qInstallMessageHandler(_qt_message_handler)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QTabWidget, QStackedWidget,
    QFrame, QLabel, QSizePolicy, QStatusBar, QPushButton
)
from PySide6.QtCore import Qt, QThreadPool, QDate, QPoint
from PySide6.QtGui import QFont, QIcon
import qtawesome as qta

import helper.theme_system as theme
from configs import config_manager
from helper.logger import logger

from widgets.sidebar import Sidebar
from widgets.filter_bar import FilterBar
from widgets.holiday_list import HolidayList
from widgets.calendar_view import CalendarView
from widgets.detail_panel import DetailPanel
from widgets.logs_panel import LogsPanel
from widgets.config_tab import ConfigTab
from widgets.search_tab import SearchTab
from workers.api_worker import HolidayWorker, CountriesWorker, WorldHolidayWorker


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self._is_maximized = False
        self.setObjectName("title_bar")
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            QWidget#title_bar {{
                background-color: {theme.color('surface')};
                border-bottom: 1px solid {theme.color('border')};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(8)

        # App icon
        icon_lbl = QLabel()
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        try:
            # prefer bundled .ico asset if available
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.ico")
            if os.path.exists(ico_path):
                icon_lbl.setPixmap(QIcon(ico_path).pixmap(16, 16))
            else:
                icon_lbl.setPixmap(qta.icon("fa5s.calendar-alt", color=theme.color("accent")).pixmap(16, 16))
        except Exception:
            pass

        # Title
        app_name = config_manager.get_app("name", "Holiday Explorer")
        app_version = config_manager.get_app("version", "1.0.0")
        self._title_lbl = QLabel(f"{app_name} \u2014 v{app_version}")
        self._title_lbl.setStyleSheet(
            f"color: {theme.color('text_muted')}; "
            f"font-size: {theme.font_size('size_small')}px; "
            "background: transparent; border: none;"
        )

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer.setStyleSheet("background: transparent; border: none;")

        min_btn  = self._make_ctrl_btn("fa5s.window-minimize",  theme.color("text_muted"),    self._minimize)
        self._max_btn = self._make_ctrl_btn("fa5s.window-maximize", theme.color("text_muted"), self._toggle_max)
        close_btn = self._make_ctrl_btn("fa5s.times",             "#ff4455",                  self._close,
                                         hover_bg="#c0392b")

        layout.addWidget(icon_lbl)
        layout.addWidget(self._title_lbl)
        layout.addWidget(spacer, 1)
        layout.addWidget(min_btn)
        layout.addWidget(self._max_btn)
        layout.addWidget(close_btn)

    def _make_ctrl_btn(self, icon_name, color, callback, hover_bg=None):
        btn = QPushButton()
        btn.setFixedSize(38, 38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hbg = hover_bg or theme.color("surface_overlay")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{ background-color: {hbg}; }}
        """)
        try:
            btn.setIcon(qta.icon(icon_name, color=color))
        except Exception:
            pass
        btn.clicked.connect(callback)
        return btn

    def _minimize(self):
        self.window().showMinimized()

    def _toggle_max(self):
        w = self.window()
        if self._is_maximized or w.isMaximized():
            w.showNormal()
            self._is_maximized = False
        else:
            w.showMaximized()
            self._is_maximized = True

    def _close(self):
        self.window().close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            if self._is_maximized or self.window().isMaximized():
                self.window().showNormal()
                self._is_maximized = False
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_max()
        super().mouseDoubleClickEvent(event)


class HolidaysTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.filter_bar = FilterBar()

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme.color('border')}; border: none;")

        self.view_stack = QStackedWidget()
        self.holiday_list = HolidayList()
        self.calendar_view = CalendarView()
        self.view_stack.addWidget(self.holiday_list)
        self.view_stack.addWidget(self.calendar_view)

        self.detail_panel = DetailPanel()

        # Horizontal splitter: list/calendar | detail panel
        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.center_splitter.setHandleWidth(3)
        self.center_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {theme.color('border')};
            }}
            QSplitter::handle:hover {{
                background-color: {theme.color('accent')};
            }}
        """)
        self.center_splitter.addWidget(self.view_stack)
        self.center_splitter.addWidget(self.detail_panel)
        # collapsible after adding widgets
        self.center_splitter.setCollapsible(0, False)
        self.center_splitter.setCollapsible(1, True)
        self.center_splitter.setStretchFactor(0, 1)
        self.center_splitter.setStretchFactor(1, 0)
        self.center_splitter.setSizes([800, 300])

        layout.addWidget(self.filter_bar)
        layout.addWidget(separator)
        layout.addWidget(self.center_splitter, 1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._thread_pool = QThreadPool.globalInstance()
        self._current_year = config_manager.get_ui("last_year", 2026)
        self._current_month = config_manager.get_ui("last_month", 1)
        self._current_country = config_manager.get_ui("last_country", config_manager.get_default_country())
        self._holidays = []
        # In-memory cache: (country, year, month) -> list of holidays
        self._memory_cache: dict = {}
        # Accumulated sidebar counts: (country, year) -> {month: count}
        self._month_counts: dict = {}
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._post_init()

    def _setup_window(self):
        app_name = config_manager.get_app("name", "Holiday Explorer")
        app_version = config_manager.get_app("version", "1.0.0")
        self.setWindowTitle(f"{app_name} v{app_version}")
        # Remove native title bar; use custom TitleBar widget
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        w = config_manager.get_ui("window_width", 1280)
        h = config_manager.get_ui("window_height", 800)
        self.resize(w, h)
        self.setMinimumSize(900, 600)
        try:
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.ico")
            if os.path.exists(ico_path):
                self.setWindowIcon(QIcon(ico_path))
            else:
                self.setWindowIcon(qta.icon("fa5s.calendar-alt", color=theme.color("accent")))
        except Exception:
            pass

    def _setup_ui(self):
        self.setStyleSheet(theme.build_stylesheet())

        central = QWidget()
        central.setStyleSheet(f"background-color: {theme.color('background')};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._title_bar = TitleBar(self)
        root_layout.addWidget(self._title_bar)

        _splitter_style = f"""
            QSplitter::handle {{
                background-color: {theme.color('border')};
            }}
            QSplitter::handle:hover {{
                background-color: {theme.color('accent')};
            }}
        """

        # Horizontal splitter: sidebar | center
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(3)
        main_splitter.setStyleSheet(_splitter_style)

        self._sidebar = Sidebar()
        sidebar_width = config_manager.get_ui("sidebar_width", 200)
        self._sidebar.setMinimumWidth(0)
        self._sidebar.setMaximumWidth(400)
        main_splitter.addWidget(self._sidebar)

        self._center_widget = self._build_center()
        main_splitter.addWidget(self._center_widget)

        # now that widgets exist, configure collapsibility
        main_splitter.setCollapsible(0, True)
        main_splitter.setCollapsible(1, False)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([sidebar_width, 1000])
        self._main_splitter = main_splitter

        # Vertical splitter: (sidebar+center) | logs
        self._logs_panel = LogsPanel()
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(3)
        v_splitter.setStyleSheet(_splitter_style)
        v_splitter.addWidget(main_splitter)
        v_splitter.addWidget(self._logs_panel)
        # configure collapsibility after adding
        v_splitter.setCollapsible(0, False)
        v_splitter.setCollapsible(1, True)
        v_splitter.setStretchFactor(0, 1)
        v_splitter.setStretchFactor(1, 0)
        v_splitter.setSizes([700, 140])
        self._v_splitter = v_splitter

        root_layout.addWidget(v_splitter, 1)

        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {theme.color('surface')};
                color: {theme.color('text_secondary')};
                border-top: 1px solid {theme.color('border')};
                font-size: {theme.font_size('size_small')}px;
            }}
        """)
        self.setStatusBar(self._status_bar)

        left_status = QLabel()
        try:
            left_status.setPixmap(qta.icon("fa5s.circle", color=theme.color("success")).pixmap(8, 8))
        except Exception:
            pass
        self._status_bar.addPermanentWidget(left_status)

        self._status_text = QLabel("Ready")
        self._status_bar.addWidget(self._status_text)

    def _build_center(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background-color: {theme.color('background')};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {theme.color('surface')};
                border: none;
            }}
            QTabBar::tab {{
                background-color: {theme.color('tab_bg')};
                color: {theme.color('text_secondary')};
                padding: 8px 22px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {theme.font_size('size_normal')}px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme.color('surface')};
                color: {theme.color('accent')};
                border-bottom: 2px solid {theme.color('accent')};
            }}
            QTabBar::tab:hover {{
                background-color: {theme.color('surface_raised')};
                color: {theme.color('text_primary')};
            }}
        """)

        self._holidays_tab = HolidaysTab()
        self._config_tab = ConfigTab()
        self._search_tab = SearchTab()

        holidays_icon = None
        config_icon = None
        search_icon = None
        try:
            holidays_icon = qta.icon("fa5s.calendar-check", color=theme.color("text_secondary"))
            config_icon = qta.icon("fa5s.cog", color=theme.color("text_secondary"))
            search_icon = qta.icon("fa5s.search", color=theme.color("text_secondary"))
        except Exception:
            pass

        if holidays_icon:
            self._tab_widget.addTab(self._holidays_tab, holidays_icon, "Holidays")
            self._tab_widget.addTab(self._search_tab, search_icon, "Search")
            self._tab_widget.addTab(self._config_tab, config_icon, "Configuration")
        else:
            self._tab_widget.addTab(self._holidays_tab, "Holidays")
            self._tab_widget.addTab(self._search_tab, "Search")
            self._tab_widget.addTab(self._config_tab, "Configuration")

        layout.addWidget(self._tab_widget)
        return container

    def _connect_signals(self):
        self._sidebar.month_selected.connect(self._on_month_selected)
        self._sidebar.year_changed.connect(self._on_year_changed)

        fb = self._holidays_tab.filter_bar
        fb.country_changed.connect(self._on_country_changed)
        fb.search_changed.connect(self._on_search_changed)
        fb.view_mode_changed.connect(self._on_view_mode_changed)
        fb.refresh_requested.connect(self._on_refresh)

        hl = self._holidays_tab.holiday_list
        hl.holiday_selected.connect(self._on_holiday_selected)

        cv = self._holidays_tab.calendar_view
        cv.date_clicked.connect(self._on_calendar_date_clicked)

        dp = self._holidays_tab.detail_panel
        dp.close_requested.connect(self._on_detail_closed)
        dp.search_platform_requested.connect(self._on_search_platform_requested)

        self._config_tab.config_saved.connect(self._on_config_saved)

    def _post_init(self):
        self._sidebar.set_year(self._current_year)
        # Default to All Year (month -1 in sidebar, 0 in app)
        saved_month = config_manager.get_ui("last_month", 0)
        self._current_month = saved_month
        sidebar_sel = -1 if saved_month == 0 else saved_month - 1
        self._sidebar.set_selected_month(sidebar_sel)
        self._holidays_tab.filter_bar.set_view_mode(config_manager.get_ui("view_mode", "list"))
        self._on_view_mode_changed(config_manager.get_ui("view_mode", "list"))
        self._load_countries()

    def _load_countries(self):
        worker = CountriesWorker()
        worker.signals.finished.connect(self._on_countries_loaded)
        self._thread_pool.start(worker)

    def _on_countries_loaded(self, countries: list):
        self._holidays_tab.filter_bar.populate_countries(countries)
        self._holidays_tab.filter_bar.set_country(self._current_country)
        self._trigger_load()

    def _trigger_load(self, force: bool = False):
        key = (self._current_country, self._current_year, self._current_month)
        if not force:
            # 1. Check in-memory cache first (instant)
            if key in self._memory_cache:
                self._on_holidays_loaded(self._memory_cache[key])
                return
            # 2. Check DB/JSON cache synchronously — avoids spawning a thread when data
            #    is already persisted (e.g. after a World fetch or on restart)
            import helper.cache_manager as cm
            cached = cm.get_holidays(self._current_country, self._current_year, self._current_month)
            if cached is not None:
                self._memory_cache[key] = cached
                self._on_holidays_loaded(cached)
                return
        label = "All Year" if self._current_month == 0 else f"{self._current_month:02d}"
        self._set_status(f"Loading {self._current_year}/{label} for {self._current_country}...")
        self._holidays_tab.holiday_list.show_loading()
        if self._current_country == "WORLD":
            worker = WorldHolidayWorker(self._current_year, self._current_month)
        else:
            worker = HolidayWorker(self._current_country, self._current_year, self._current_month)
        worker.signals.status.connect(self._set_status)
        worker.signals.finished.connect(self._on_holidays_loaded)
        worker.signals.cached.connect(self._on_holidays_loaded)
        worker.signals.error.connect(self._on_load_error)
        self._thread_pool.start(worker)

    def _on_month_selected(self, month: int):
        # month: 0 = All Year, 1-12 = specific month
        self._current_month = month
        config_manager.set_ui("last_month", month)
        if month != 0:
            self._holidays_tab.calendar_view.set_month(self._current_year, month)
        self._trigger_load()

    def _on_year_changed(self, year: int):
        self._current_year = year
        config_manager.set_ui("last_year", year)
        if self._current_month != 0:
            self._holidays_tab.calendar_view.set_month(year, self._current_month)
        self._trigger_load()

    def _on_country_changed(self, code: str):
        self._current_country = code
        config_manager.set_ui("last_country", code)
        self._trigger_load()

    def _on_search_changed(self, text: str):
        self._holidays_tab.holiday_list.set_search(text)

    def _on_view_mode_changed(self, mode: str):
        config_manager.set_ui("view_mode", mode)
        if mode == "list":
            self._holidays_tab.view_stack.setCurrentWidget(self._holidays_tab.holiday_list)
        else:
            self._holidays_tab.view_stack.setCurrentWidget(self._holidays_tab.calendar_view)
            if self._current_month != 0:
                self._holidays_tab.calendar_view.set_month(self._current_year, self._current_month)
            self._holidays_tab.calendar_view.set_holidays(self._holidays)

    def _on_refresh(self):
        import helper.cache_manager as cm
        cm.clear_all()
        self._memory_cache.clear()
        self._month_counts.clear()
        logger.info(f"Cache cleared. Forcing reload for {self._current_country} {self._current_year}/{self._current_month}")
        self._trigger_load(force=True)

    def _on_holidays_loaded(self, holidays: list):
        self._holidays = holidays
        self._holidays_tab.holiday_list.set_holidays(holidays)
        self._holidays_tab.calendar_view.set_holidays(holidays)
        count = len(holidays)
        label = "All Year" if self._current_month == 0 else f"{self._current_month:02d}"
        self._set_status(f"{count} holidays loaded for {self._current_country} {self._current_year}/{label}")
        logger.info(f"UI updated: {count} holidays displayed")

        # Save into in-memory cache so next switch is instant
        key = (self._current_country, self._current_year, self._current_month)
        self._memory_cache[key] = holidays

        # Accumulate per-month counts in sidebar (never wipe other months)
        from collections import Counter
        ck = (self._current_country, self._current_year)
        if ck not in self._month_counts:
            self._month_counts[ck] = {}
        if self._current_month == 0:
            # All-Year load: recalculate all months from this full dataset
            counts = Counter()
            for h in holidays:
                try:
                    m = int(h.get("date_month") or h.get("date", "").split("-")[1])
                    counts[m] += 1
                except Exception:
                    pass
            self._month_counts[ck] = dict(counts)
        else:
            # Single month: only update that month's slot
            self._month_counts[ck][self._current_month] = count
        self._sidebar.set_month_counts(self._month_counts[ck])

    def _on_load_error(self, error: str):
        self._holidays_tab.holiday_list.show_error(error)
        self._set_status(f"Error: {error[:60]}")

    def _on_holiday_selected(self, holiday: dict):
        self._holidays_tab.detail_panel.show_holiday(holiday)
        self._search_tab.set_holiday(holiday)

    def _on_search_platform_requested(self, platform_id: str, keyword: str):
        self._search_tab.set_holiday(self._holidays_tab.detail_panel._holiday)
        self._search_tab.switch_to_platform(platform_id)
        idx = self._tab_widget.indexOf(self._search_tab)
        self._tab_widget.setCurrentIndex(idx)

    def _on_calendar_date_clicked(self, date_str: str, holidays: list):
        self._holidays_tab.detail_panel.show_date_holidays(date_str, holidays)

    def _on_detail_closed(self):
        pass

    def _on_config_saved(self):
        self._set_status("Configuration saved. Reloading countries...")
        self._load_countries()

    def _set_status(self, text: str):
        self._status_text.setText(text)

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            import ctypes
            from ctypes import windll, wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                pos = wintypes.POINT()
                windll.user32.GetCursorPos(ctypes.byref(pos))
                rect = wintypes.RECT()
                windll.user32.GetWindowRect(int(self.winId()), ctypes.byref(rect))
                B = 6
                l = pos.x < rect.left   + B
                r = pos.x > rect.right  - B
                t = pos.y < rect.top    + B
                b = pos.y > rect.bottom - B
                if t and l: return True, 13  # HTTOPLEFT
                if t and r: return True, 14  # HTTOPRIGHT
                if b and l: return True, 16  # HTBOTTOMLEFT
                if b and r: return True, 17  # HTBOTTOMRIGHT
                if t:       return True, 12  # HTTOP
                if b:       return True, 15  # HTBOTTOM
                if l:       return True, 10  # HTLEFT
                if r:       return True, 11  # HTRIGHT
        return super().nativeEvent(event_type, message)

    def closeEvent(self, event):
        w, h = self.width(), self.height()
        config_manager.set_ui("window_width", w)
        config_manager.set_ui("window_height", h)
        config_manager.save()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Holiday Explorer")
    app.setOrganizationName("HolidayExplorer")
    app.setStyleSheet(theme.build_stylesheet())

    font = QFont(theme.font_family(), theme.font_size("size_normal"))
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
