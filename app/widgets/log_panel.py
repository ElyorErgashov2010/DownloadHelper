"""Log paneli (faqat o'qish uchun), oxirgi qatorni yangilash imkoniyati bilan."""

from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QFont, QTextCursor


class LogPanel(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setMaximumBlockCount(5000)
        self._last_progress_text = ""

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
