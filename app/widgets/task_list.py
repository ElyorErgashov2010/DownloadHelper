"""Vazifalar tarixi jadvali."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Signal

from app.core.task_manager import Task

_STATUS_UZ = {
    "Pending": "Kutilmoqda",
    "Downloading": "Yuklanmoqda",
    "Uploading": "S3 ga yuborilmoqda",
    "Done": "Tayyor",
    "Failed": "Xato",
}


class TaskList(QWidget):
    view_logs_requested = Signal(int)
    redownload_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nomi", "Holat", "Sana", "Manzil"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.view_logs_btn = QPushButton("Loglarni ko'rsatish")
        self.redownload_btn = QPushButton("Qayta yuklab olish")
        self.delete_btn = QPushButton("O'chirish")
        btn_layout.addWidget(self.view_logs_btn)
        btn_layout.addWidget(self.redownload_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._task_ids: list[int] = []

        self.view_logs_btn.clicked.connect(self._on_view_logs)
        self.redownload_btn.clicked.connect(self._on_redownload)
        self.delete_btn.clicked.connect(self._on_delete)

    def load_tasks(self, tasks: list[Task]):
        self.table.setRowCount(0)
        self._task_ids.clear()
        for task in tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(task.name))
            status_uz = _STATUS_UZ.get(task.status, task.status)
            self.table.setItem(row, 1, QTableWidgetItem(status_uz))
            date_str = task.created_at.split(" ")[0] if task.created_at else ""
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
            dest = "S3" if task.destination_type == "s3" else "Lokal"
            self.table.setItem(row, 3, QTableWidgetItem(dest))
            self._task_ids.append(task.id)

    def _selected_task_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            return self._task_ids[rows[0].row()]
        return None

    def _on_view_logs(self):
        tid = self._selected_task_id()
        if tid is not None:
            self.view_logs_requested.emit(tid)

    def _on_redownload(self):
        tid = self._selected_task_id()
        if tid is not None:
            self.redownload_requested.emit(tid)

    def _on_delete(self):
        tid = self._selected_task_id()
        if tid is not None:
            self.delete_requested.emit(tid)
