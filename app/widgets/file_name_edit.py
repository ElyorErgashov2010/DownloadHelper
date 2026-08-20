"""Fayl nomi muharriri va «Normallashtirish» tugmasi."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton


class FileNameEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Fayl nomi:"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Fayl nomi (kengaytmasiz)")
        layout.addWidget(self.line_edit, 1)

        self.normalize_btn = QPushButton("Normallashtirish")
        layout.addWidget(self.normalize_btn)

    def get_name(self) -> str:
        return self.line_edit.text().strip()

    def set_name(self, name: str):
        self.line_edit.setText(name)
