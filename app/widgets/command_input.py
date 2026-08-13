"""Buyruq kiritish vidjeti: qo'yilganda avtomatik tahlil qiladi."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal


class _PasteAwareTextEdit(QTextEdit):
    """Matn qo'yilganda signal beradigan QTextEdit."""
    pasted = pyqtSignal()

    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.pasted.emit()


class CommandInput(QWidget):
    # Signal: matn qo'yish orqali o'zgardi — tahlil qilish vaqti
    auto_parse_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(
            'Ishga tushirish buyrug\'ini olish uchun System Log (JSON) faylini '
            'Telegramdagi <a href="https://t.me/kinescopedownloader_robot">@kinescopedownloader_robot</a> '
            'botiga yuboring'
        )
        hint.setWordWrap(True)
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("color: gray; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(hint)

        label = QLabel("Buyruq:")
        layout.addWidget(label)

        self.text_edit = _PasteAwareTextEdit()
        self.text_edit.setPlaceholderText("N_m3u8DL-RE buyrug'ini shu yerga qo'ying...")
        self.text_edit.setMaximumHeight(100)
        self.text_edit.pasted.connect(self._on_pasted)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.parse_btn = QPushButton("Buyruqni tahlil qilish")
        btn_layout.addWidget(self.parse_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_pasted(self):
        self.auto_parse_requested.emit()

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def set_text(self, text: str):
        self.text_edit.setPlainText(text)
