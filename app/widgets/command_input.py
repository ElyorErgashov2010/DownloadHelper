"""Buyruq kiritish vidjeti: «Joylash» orqali qo'yilgan buyruqni tahlil qiladi."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.widgets.slim_scrollbar import SlimVerticalScrollBar


class _PasteAwareTextEdit(QTextEdit):
    """Matn qo'yilganda signal beradigan QTextEdit."""

    pasted = Signal()

    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.pasted.emit()


class CommandInput(QWidget):
    # Signal: matn qo'yildi — tahlil qilish vaqti
    auto_parse_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(
            "Ishga tushirish buyrug'ini olish uchun System Log (JSON) faylini "
            'Telegramdagi <a href="https://t.me/kinescopedownloader_robot">@kinescopedownloader_robot</a> '
            "botiga yuboring"
        )
        hint.setWordWrap(True)
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("color: gray; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(hint)

        layout.addWidget(QLabel("Buyruq:"))

        self.text_edit = _PasteAwareTextEdit()
        self.text_edit.setPlaceholderText("N_m3u8DL-RE buyrug'ini shu yerga qo'ying...")
        # Kichik oynada buyruq maydoni yo'qolib ketmasligi uchun doimiy balandlik.
        self.text_edit.setFixedHeight(100)
        self.text_edit.setVerticalScrollBar(
            SlimVerticalScrollBar(framed_on_hover=True, extent=18)
        )
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.pasted.connect(self._on_pasted)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.parse_btn = QPushButton("Buyruqni tahlil qilish")
        self.paste_btn = QPushButton("Joylash")
        self.paste_btn.setToolTip("Almashinuv buferidagi matnni joylash (Ctrl+V)")
        btn_layout.addWidget(self.parse_btn)
        btn_layout.addWidget(self.paste_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_pasted(self):
        self.auto_parse_requested.emit()

    def paste_from_clipboard(self) -> bool:
        """Matn maydoniga odatiy Ctrl+V kabi almashinuv buferini joylaydi."""
        if not self.text_edit.canPaste():
            return False
        self.text_edit.paste()
        return True

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def set_text(self, text: str):
        self.text_edit.setPlainText(text)
