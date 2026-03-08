from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QTextCursor, QColor
import qtawesome as qta
import theme_system as theme
from logger import logger


LEVEL_STYLES = {
    "INFO":    ("#4499ff", "fa5s.info-circle"),
    "SUCCESS": ("#44bb77", "fa5s.check-circle"),
    "WARNING": ("#ffaa00", "fa5s.exclamation-triangle"),
    "ERROR":   ("#ff4455", "fa5s.times-circle"),
    "API":     ("#aa77ff", "fa5s.cloud"),
    "CACHE":   ("#00cccc", "fa5s.database"),
}


class LogsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_lines = 500
        self._setup_ui()
        logger.log_emitted.connect(self._on_log)

    def _setup_ui(self):
        self.setFixedHeight(140)
        self.setObjectName("logs_panel_root")
        self.setStyleSheet(f"""
            QWidget#logs_panel_root {{
                background-color: {theme.color('log_bg')};
                border-top: 1px solid {theme.color('border')};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("log_header")
        header.setFixedHeight(32)
        header.setStyleSheet(f"""
            QFrame#log_header {{
                background-color: {theme.color('surface')};
                border-bottom: 1px solid {theme.color('border')};
                border-top: none;
                border-left: none;
                border-right: none;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)

        icon_lbl = QLabel()
        try:
            icon_lbl.setPixmap(qta.icon("fa5s.terminal", color=theme.color("text_muted")).pixmap(14, 14))
        except Exception:
            pass
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        title = QLabel("Runtime Logs")
        font = QFont(theme.font_family(), theme.font_size("size_small"))
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet(f"color: {theme.color('text_muted')}; background: transparent; letter-spacing: 1px; border: none;")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton()
        clear_btn.setFixedSize(24, 24)
        clear_btn.setToolTip("Clear logs")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {theme.color('border')};
                border-radius: {theme.radius('small')}px;
            }}
            QPushButton:hover {{
                border: 1px solid {theme.color('accent')};
                background-color: {theme.color('accent_dim')};
            }}
        """)
        try:
            clear_btn.setIcon(qta.icon("fa5s.trash-alt", color=theme.color("text_muted")))
        except Exception:
            clear_btn.setText("X")
        clear_btn.clicked.connect(self._clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.color('log_bg')};
                color: {theme.color('log_text')};
                font-family: "Consolas", "Courier New", monospace;
                font-size: {theme.font_size('size_small')}px;
                border: none;
                padding: 4px 10px;
            }}
        """)
        layout.addWidget(self._log_view, 1)

    @Slot(str, str)
    def _on_log(self, level: str, entry: str):
        color, _ = LEVEL_STYLES.get(level, ("#999999", "fa5s.circle"))
        self._log_view.moveCursor(QTextCursor.MoveOperation.End)
        self._log_view.setTextColor(QColor(color))
        self._log_view.insertPlainText(entry + "\n")
        self._log_view.moveCursor(QTextCursor.MoveOperation.End)
        self._trim()

    def _trim(self):
        doc = self._log_view.document()
        while doc.blockCount() > self._max_lines:
            cursor = QTextCursor(doc.begin())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()

    def _clear(self):
        self._log_view.clear()
