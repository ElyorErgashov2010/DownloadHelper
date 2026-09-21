"""Log paneli: faqat o'qish uchun va ixtiyoriy balandlik resize tutqichi bilan."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from app.widgets.slim_scrollbar import SlimVerticalScrollBar


class _LogResizeHandle(QWidget):
    """Logning pastki o'ng burchagidagi tortib kattalashtirish tutqichi."""

    SIZE = 18

    def __init__(self, log_panel):
        super().__init__(log_panel.viewport())
        self._log_panel = log_panel
        self._start_global_y = 0
        self._start_height = 0
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setToolTip("Log maydonini kattalashtirish yoki kichraytirish uchun torting")
        self.raise_()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#a8a8a8"), 1))
        # HTML textarea'dagi resize belgisi kabi uchta diagonal chiziq.
        for offset in (5, 9, 13):
            painter.drawLine(offset, self.height() - 3, self.width() - 3, offset)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_global_y = round(event.globalPosition().y())
            self._start_height = self._log_panel.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_global_y:
            delta = round(event.globalPosition().y()) - self._start_global_y
            self._log_panel.set_user_height(self._start_height + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_global_y = 0
            self._start_height = 0
            event.accept()
            return
        super().mouseReleaseEvent(event)


class LogPanel(QPlainTextEdit):
    """Log paneli (faqat o'qish uchun), oxirgi qatorni yangilash imkoniyati bilan."""

    _MIN_USER_HEIGHT = 150
    _MAX_USER_HEIGHT = 1000

    def __init__(self, parent=None, *, resizable: bool = False):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setMaximumBlockCount(5000)
        self.setMinimumHeight(self._MIN_USER_HEIGHT)
        self.setVerticalScrollBar(
            SlimVerticalScrollBar(framed_on_hover=True, extent=18)
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._last_progress_text = ""
        self._resize_handle = _LogResizeHandle(self) if resizable else None
        if self._resize_handle:
            self._position_resize_handle()
            self._resize_handle.show()

    def _position_resize_handle(self):
        if not self._resize_handle:
            return
        viewport = self.viewport()
        self._resize_handle.move(
            max(0, viewport.width() - self._resize_handle.width() - 1),
            max(0, viewport.height() - self._resize_handle.height() - 1),
        )
        self._resize_handle.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_resize_handle()

    def set_user_height(self, height: int):
        """Foydalanuvchi tortgan balandlikni layout uchun saqlaydi."""
        new_height = max(self._MIN_USER_HEIGHT, min(self._MAX_USER_HEIGHT, height))
        self.setMinimumHeight(new_height)
        self.setMaximumHeight(new_height)
        self.updateGeometry()
        parent = self.parentWidget()
        if parent and parent.layout():
            parent.layout().invalidate()
        self._position_resize_handle()

    def append_text(self, text: str):
        """Matnni log oxiriga qo'shish."""
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)

    def replace_last_line(self, text: str):
        """Oxirgi qatorni almashtirish (jarayon uchun). Takrorlarni o'tkazib yuboradi."""
        if text == self._last_progress_text:
            return
        self._last_progress_text = text
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.moveCursor(QTextCursor.MoveOperation.End)
