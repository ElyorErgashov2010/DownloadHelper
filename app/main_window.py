"""«Yangi vazifa» va «Tarix» varaqlari bo'lgan asosiy oyna."""

import os
import shutil
import tempfile
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QSpinBox, QFileDialog, QListWidget,
    QListWidgetItem, QCheckBox, QApplication,
)
from PyQt6.QtCore import QSize, Qt, QTimer

from app.core.command_parser import parse_command, ParsedCommand
from app.core.normalizer import normalize_filename
from app.core.config import ConfigManager
from app.core.task_manager import TaskManager, Task
from app.core.downloader import Downloader, find_executable, check_all_tools, format_tool_check_log
from app.core.s3_uploader import S3Uploader
from app.core.notifier import Notifier
from app.widgets.command_input import CommandInput
from app.widgets.file_name_edit import FileNameEdit
from app.widgets.destination_panel import DestinationPanel
from app.widgets.log_panel import LogPanel
from app.widgets.progress_panel import ProgressPanel
from app.widgets.task_list import TaskList
from app.dialogs.s3_config_dialog import S3ConfigDialog
from app.dialogs.help_dialog import HelpDialog


@dataclass
class QueueItem:
    """Yuklab olish navbati elementi."""
    raw_command: str
    parsed: ParsedCommand
    name: str
    save_dir: str
    dest_type: str          # "local" / "s3"
    dest_path: str
    delete_local: bool
    s3_profile: str = ""
    task_id: int | None = None
    retries_left: int = 0
    local_file: str = ""    # yuklab olingan fayl yo'li (S3 qayta urinish uchun)
    s3_retry_only: bool = False  # faqat S3 qayta urinish (yuklab olmasdan)


@dataclass
class S3Failure:
    """S3 ga yuklash muvaffaqiyatsizligi haqida ma'lumot."""
    item: QueueItem
    error: str


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yuklab olish yordamchisi")
        self.setMinimumSize(QSize(700, 600))

        self._config = ConfigManager()
        self._task_mgr = TaskManager()
        self._downloader = Downloader(self)
        self._notifier = Notifier()
        self._uploader: S3Uploader | None = None
        self._cancelling = False
        self._current_item: QueueItem | None = None
        self._queue: list[QueueItem] = []
        self._s3_failures: list[S3Failure] = []
        self._parsed: ParsedCommand | None = None

        # Jarayon yangilanishini cheklash (200 ms da bir martadan ko'p emas)
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(200)
        self._progress_timer.timeout.connect(self._flush_progress)
        self._stream_lines: dict[str, str] = {}
        self._stream_pri = {"vid": 3, "aud": 2, "sub": 1}
        self._full_log: list[str] = []  # BD ga saqlash uchun to'liq log

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(6, 6, 6, 6)

        # Avto-rejim va yordam tugmasi bo'lgan yuqori qator
        top_row = QHBoxLayout()
        self._auto_cb = QCheckBox("Avto-rejim")
        self._auto_cb.toggled.connect(self._on_auto_toggle)
        top_row.addWidget(self._auto_cb)

        self._auto_normalize_cb = QCheckBox("Nomni avto-normallashtirish")
        self._auto_normalize_cb.setChecked(True)
        self._auto_normalize_cb.setEnabled(False)
        top_row.addWidget(self._auto_normalize_cb)

        auto_help_btn = QPushButton("?")
        auto_help_btn.setFixedSize(22, 22)
        auto_help_btn.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 11px; border-radius: 11px; }"
        )
        auto_help_btn.clicked.connect(self._on_auto_help)
        top_row.addWidget(auto_help_btn)

        top_row.addStretch()
        help_btn = QPushButton("?")
        help_btn.setFixedSize(28, 28)
        help_btn.setToolTip("Yordam")
        help_btn.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14px; border-radius: 14px; }"
        )
        help_btn.clicked.connect(self._on_help)
        top_row.addWidget(help_btn)
        central_layout.addLayout(top_row)

        # Almashinuv buferini kuzatish
        self._clipboard = QApplication.clipboard()
        self._ignore_clipboard = False

        self._tabs = QTabWidget()
        central_layout.addWidget(self._tabs, 1)

        github_link = QLabel(
            '<a href="https://github.com/ElyorErgashov2010/DownloadHelper/releases">'
            'github.com/ElyorErgashov2010/DownloadHelper/releases</a>'
        )
        github_link.setOpenExternalLinks(True)
        github_link.setAlignment(github_link.alignment())
        github_link.setStyleSheet("color: gray; font-size: 11px; padding: 2px 0;")
        central_layout.addWidget(github_link)

        self.setCentralWidget(central)

        self._build_new_task_tab()
        self._build_history_tab()

        self._downloader.log_received.connect(self._on_download_log)
        self._downloader.progress_received.connect(self._on_download_progress)
        self._downloader.finished.connect(self._on_download_finished)

        # S3 profillarini kombo-boksga yuklash
        self._refresh_s3_profiles()

    # ── «Yangi vazifa» varag'i ───────────────────────────────────

    def _build_new_task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._cmd_input = CommandInput()
        self._cmd_input.parse_btn.clicked.connect(self._on_parse)
        self._cmd_input.auto_parse_requested.connect(self._on_parse)
        layout.addWidget(self._cmd_input)

        self._file_name = FileNameEdit()
        self._file_name.normalize_btn.clicked.connect(self._on_normalize)
        layout.addWidget(self._file_name)

        layout.addWidget(QLabel("Saqlash joyi:"))
        self._dest_panel = DestinationPanel(self._config.get("save_path"))
        self._dest_panel.s3_settings_btn.clicked.connect(self._on_s3_settings)
        self._dest_panel.set_s3_path(self._config.get("s3_default_path"))
        layout.addWidget(self._dest_panel)

        # Qator: qayta urinishlar + tugmalar
        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("Xato bo'lsa qayta urinishlar:"))
        self._retry_spin = QSpinBox()
        self._retry_spin.setRange(0, 10)
        self._retry_spin.setValue(2)
        self._retry_spin.setToolTip("Yuklashda xato bo'lsa qayta urinishlar soni")
        ctrl_row.addWidget(self._retry_spin)

        ctrl_row.addSpacing(20)

        self._add_queue_btn = QPushButton("Navbatga qo'shish")
        self._download_btn = QPushButton("Yuklab olish")
        self._stop_btn = QPushButton("Bekor qilish")
        self._stop_btn.setEnabled(False)
        ctrl_row.addWidget(self._add_queue_btn)
        ctrl_row.addWidget(self._download_btn)
        ctrl_row.addWidget(self._stop_btn)
        ctrl_row.addStretch()
        layout.addLayout(ctrl_row)

        # Ochiladigan navbat
        queue_header = QHBoxLayout()
        self._queue_toggle = QPushButton("▶ Navbat (0)")
        self._queue_toggle.setStyleSheet(
            "QPushButton { border: none; color: gray; font-size: 12px; text-align: left; }"
        )
        self._queue_toggle.setCheckable(True)
        self._queue_toggle.clicked.connect(self._on_toggle_queue)
        queue_header.addWidget(self._queue_toggle)
        queue_header.addStretch()
        self._queue_remove_btn = QPushButton("Tanlanganni o'chirish")
        self._queue_remove_btn.setVisible(False)
        self._queue_remove_btn.clicked.connect(self._on_remove_from_queue)
        queue_header.addWidget(self._queue_remove_btn)
        self._queue_clear_btn = QPushButton("Tozalash")
        self._queue_clear_btn.setVisible(False)
        self._queue_clear_btn.clicked.connect(self._on_clear_queue)
        queue_header.addWidget(self._queue_clear_btn)
        layout.addLayout(queue_header)

        self._queue_list = QListWidget()
        self._queue_list.setMaximumHeight(120)
        self._queue_list.setVisible(False)
        self._queue_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self._queue_list)

        self._add_queue_btn.clicked.connect(self._on_add_to_queue)
        self._download_btn.clicked.connect(self._on_download)
        self._stop_btn.clicked.connect(self._on_stop)

        # S3 xatolari paneli
        s3_fail_header = QHBoxLayout()
        self._s3_fail_toggle = QPushButton("▶ S3 xatolari (0)")
        self._s3_fail_toggle.setStyleSheet(
            "QPushButton { border: none; color: #cc3333; font-size: 12px; "
            "text-align: left; font-weight: bold; }"
        )
        self._s3_fail_toggle.setCheckable(True)
        self._s3_fail_toggle.clicked.connect(self._on_toggle_s3_failures)
        self._s3_fail_toggle.setVisible(False)
        s3_fail_header.addWidget(self._s3_fail_toggle)
        s3_fail_header.addStretch()
        self._s3_retry_btn = QPushButton("Barchasini qayta urinish")
        self._s3_retry_btn.setVisible(False)
        self._s3_retry_btn.clicked.connect(self._on_retry_s3_all)
        s3_fail_header.addWidget(self._s3_retry_btn)
        self._s3_retry_selected_btn = QPushButton("Tanlanganlarni qayta urinish")
        self._s3_retry_selected_btn.setVisible(False)
        self._s3_retry_selected_btn.clicked.connect(self._on_retry_s3_selected)
        s3_fail_header.addWidget(self._s3_retry_selected_btn)
        self._s3_fail_clear_btn = QPushButton("Tozalash")
        self._s3_fail_clear_btn.setVisible(False)
        self._s3_fail_clear_btn.clicked.connect(self._on_clear_s3_failures)
        s3_fail_header.addWidget(self._s3_fail_clear_btn)
        layout.addLayout(s3_fail_header)

        self._s3_fail_list = QListWidget()
        self._s3_fail_list.setMaximumHeight(120)
        self._s3_fail_list.setVisible(False)
        self._s3_fail_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._s3_fail_list.setStyleSheet(
            "QListWidget { border: 1px solid #cc3333; }"
            "QListWidget::item { color: #cc3333; }"
        )
        layout.addWidget(self._s3_fail_list)

        # Progress-bar
        self._progress = ProgressPanel()
        layout.addWidget(self._progress)

        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Loglar:"))
        log_header.addStretch()
        copy_log_btn = QPushButton("Nusxalash")
        copy_log_btn.setToolTip("Logni almashinuv buferiga nusxalash")
        copy_log_btn.clicked.connect(lambda: self._copy_log(self._log_panel))
        save_log_btn = QPushButton("Saqlash")
        save_log_btn.setToolTip("Logni faylga saqlash")
        save_log_btn.clicked.connect(lambda: self._save_log(self._log_panel))
        log_header.addWidget(copy_log_btn)
        log_header.addWidget(save_log_btn)
        layout.addLayout(log_header)

        self._log_panel = LogPanel()
        layout.addWidget(self._log_panel, 1)

        self._tabs.addTab(tab, "Yangi vazifa")

    # ── «Tarix» varag'i ──────────────────────────────────────────

    def _build_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._task_list = TaskList()
        layout.addWidget(self._task_list, 1)

        hist_log_header = QHBoxLayout()
        hist_log_header.addWidget(QLabel("Vazifa loglari:"))
        hist_log_header.addStretch()
        copy_hist_btn = QPushButton("Nusxalash")
        copy_hist_btn.setToolTip("Logni almashinuv buferiga nusxalash")
        copy_hist_btn.clicked.connect(lambda: self._copy_log(self._history_log))
        save_hist_btn = QPushButton("Saqlash")
        save_hist_btn.setToolTip("Logni faylga saqlash")
        save_hist_btn.clicked.connect(lambda: self._save_log(self._history_log))
        hist_log_header.addWidget(copy_hist_btn)
        hist_log_header.addWidget(save_hist_btn)
        layout.addLayout(hist_log_header)

        self._history_log = LogPanel()
        layout.addWidget(self._history_log, 1)

        self._task_list.view_logs_requested.connect(self._on_view_task_logs)
        self._task_list.redownload_requested.connect(self._on_redownload)
        self._task_list.delete_requested.connect(self._on_delete_task)

        self._tabs.addTab(tab, "Tarix")
        self._tabs.currentChanged.connect(self._on_tab_changed)

    # ── S3 profillari ────────────────────────────────────────────

    def _refresh_s3_profiles(self):
        names = self._config.get_s3_profile_names()
        active = self._config.get_active_s3_profile()
        self._dest_panel.load_s3_profiles(names, active)

    # ── Umumiy slotlar ───────────────────────────────────────────

    def _on_parse(self):
        raw = self._cmd_input.get_text()
        if not raw:
            return
        self._parsed = parse_command(raw)
        if self._parsed.save_name:
            self._file_name.set_name(self._parsed.save_name)
        if self._parsed.url:
            self._log_panel.append_text(f"URL: {self._parsed.url}\n")
        if self._parsed.save_name:
            self._log_panel.append_text(f"Nomi: {self._parsed.save_name}\n")

    def _on_normalize(self):
        name = self._file_name.get_name()
        if name:
            self._file_name.set_name(normalize_filename(name))

    def _on_s3_settings(self):
        dlg = S3ConfigDialog(self._config, self)
        dlg.exec()
        self._refresh_s3_profiles()

    def _on_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    # ── Avto-rejim (almashinuv buferini kuzatish) ────────────────

    def _on_auto_toggle(self, checked: bool):
        self._auto_normalize_cb.setEnabled(checked)
        if checked:
            self._clipboard.dataChanged.connect(self._on_clipboard_changed)
            dest = "S3" if not self._dest_panel.is_local() else "Lokal"
            self._log_panel.append_text(
                f"Avto-rejim yoqildi. Manzil: {dest}. Buyruq kutilmoqda...\n"
            )
        else:
            try:
                self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except TypeError:
                pass
            self._log_panel.append_text("Avto-rejim o'chirildi.\n")

    def _on_auto_help(self):
        QMessageBox.information(self, "Avto-rejim", (
            "<b>Avto-rejim qanday ishlaydi:</b><br><br>"
            "1. «Avto-rejim» belgilash qutisini yoqing<br>"
            "2. Saqlash joyini sozlang (Lokal yoki S3, yo'l, profil)<br>"
            "3. N_m3u8DL-RE buyrug'ini istalgan joydan nusxalang (Ctrl+C)<br>"
            "4. Dastur avtomatik ravishda:<br>"
            "&nbsp;&nbsp;— buyruqni qo'yadi va tahlil qiladi<br>"
            "&nbsp;&nbsp;— fayl nomini normallashtiradi (yoqilgan bo'lsa)<br>"
            "&nbsp;&nbsp;— yuklashni boshlaydi yoki navbatga qo'shadi<br><br>"
            "<b>Nomni avto-normallashtirish:</b> kirillni lotinchaga "
            "o'giradi, probellarni «_» ga almashtiradi, maxsus "
            "belgilarni olib tashlaydi.<br><br>"
            "<b>Saqlash joyi:</b> joriy sozlamalar ishlatiladi "
            "(Lokal/S3, yo'l, profil). Ularni avto-rejimni yoqishdan "
            "oldin yoki istalgan vaqtda o'zgartiring."
        ))

    def _on_clipboard_changed(self):
        if self._ignore_clipboard:
            return
        text = self._clipboard.text().strip()
        if not text:
            return
        if "N_m3u8DL-RE" not in text and "n_m3u8dl-re" not in text.lower():
            return

        self._tabs.setCurrentIndex(0)
        self._cmd_input.set_text(text)
        self._on_parse()

        if not self._parsed:
            self._log_panel.append_text("Avto-rejim: buyruqni tahlil qilib bo'lmadi\n")
            self._notifier.notify("Avto-rejim", "Buyruqni tahlil qilib bo'lmadi", success=False)
            return

        # Avto-normallashtirish
        if self._auto_normalize_cb.isChecked():
            self._on_normalize()

        name = self._file_name.get_name() or "output"
        dest = "S3" if not self._dest_panel.is_local() else "Lokal"
        self._log_panel.append_text(f"Avto-rejim: {name} → {dest}\n")

        # Yuklash ketayotgan bo'lsa — navbatga qo'shamiz, aks holda darhol yuklaymiz
        if self._downloader.is_running():
            self._on_add_to_queue()
            self._notifier.notify("Navbatga", f"{name} → {dest}")
        else:
            self._on_download()
            self._notifier.notify("Yuklab olish", f"{name} → {dest}")

    # ── Navbat elementini yaratish ───────────────────────────────

    def _make_queue_item(self) -> QueueItem | None:
        """Formaning joriy holatidan QueueItem yig'adi. Xato bo'lsa None qaytaradi."""
        raw_cmd = self._cmd_input.get_text()
        if not raw_cmd:
            QMessageBox.warning(self, "Xato", "Buyruqni qo'ying.")
            return None

        if not self._parsed:
            self._parsed = parse_command(raw_cmd)

        name = self._file_name.get_name() or self._parsed.save_name or "output"
        is_local = self._dest_panel.is_local()

        save_dir = self._dest_panel.get_local_path()
        if not save_dir:
            QMessageBox.warning(self, "Xato", "Lokal papkani tanlang.")
            return None

        # Bulutli papkalar haqida ogohlantirish (OneDrive, Dropbox va h.k.)
        cloud_markers = ["OneDrive", "Dropbox", "Google Drive", "iCloudDrive"]
        for marker in cloud_markers:
            if marker.lower() in save_dir.lower():
                reply = QMessageBox.warning(
                    self, "Diqqat",
                    f"Papka {marker} ichida joylashgan.\n\n"
                    "Bulutli saqlashlar sinxronizatsiya paytida fayllarni "
                    "bloklab qo'yishi mumkin, bu esa N_m3u8DL-RE da "
                    "xatolarga olib keladi.\n\n"
                    "Lokal papkadan foydalanish tavsiya etiladi, "
                    "masalan C:\\Downloads\n\n"
                    "Davom etilsinmi?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return None
                break

        dest_type = "local" if is_local else "s3"
        if is_local:
            dest_path = save_dir
        else:
            s3_raw = self._dest_panel.get_s3_path()
            # Agar yo'l papka bo'lsa (oxirgi bo'lakda kengaytma yo'q bo'lsa),
            # fayl nomini avtomatik qo'shamiz
            last_segment = s3_raw.rstrip("/").rsplit("/", 1)[-1] if s3_raw else ""
            if not last_segment or "." not in last_segment:
                file_with_ext = name if "." in name else name + ".mp4"
                dest_path = s3_raw.rstrip("/") + "/" + file_with_ext
            else:
                dest_path = s3_raw
        delete_local = (not is_local) and self._dest_panel.should_delete_local()
        s3_profile = "" if is_local else self._dest_panel.get_selected_s3_profile()

        if not is_local and not s3_profile:
            QMessageBox.warning(self, "Xato",
                                "S3 profillari yo'q. Sozlamalardan profil yarating.")
            return None

        return QueueItem(
            raw_command=raw_cmd,
            parsed=self._parsed,
            name=name,
            save_dir=save_dir,
            dest_type=dest_type,
            dest_path=dest_path,
            delete_local=delete_local,
            s3_profile=s3_profile,
            retries_left=self._retry_spin.value(),
        )

    # ── Vazifalar navbati ────────────────────────────────────────

    def _update_queue_label(self):
        n = len(self._queue)
        self._queue_toggle.setText(
            f"{'▼' if self._queue_toggle.isChecked() else '▶'} Navbat ({n})"
        )
        # Ro'yxatni yangilash
        self._queue_list.clear()
        for i, item in enumerate(self._queue):
            dest = item.dest_type.upper()
            self._queue_list.addItem(f"{i + 1}. {item.name}  [{dest}]")

    def _on_toggle_queue(self, checked: bool):
        self._queue_list.setVisible(checked)
        self._queue_remove_btn.setVisible(checked)
        self._queue_clear_btn.setVisible(checked)
        self._update_queue_label()

    def _on_remove_from_queue(self):
        rows = sorted(
            {idx.row() for idx in self._queue_list.selectedIndexes()},
            reverse=True,
        )
        for row in rows:
            if 0 <= row < len(self._queue):
                removed = self._queue.pop(row)
                self._log_panel.append_text(f"Navbatdan o'chirildi: {removed.name}\n")
        self._update_queue_label()

    def _on_clear_queue(self):
        if not self._queue:
            return
        self._queue.clear()
        self._log_panel.append_text("Navbat tozalandi.\n")
        self._update_queue_label()

    # ── S3 xatolari paneli ───────────────────────────────────────

    def _update_s3_failures_ui(self):
        n = len(self._s3_failures)
        self._s3_fail_toggle.setText(
            f"{'▼' if self._s3_fail_toggle.isChecked() else '▶'} S3 xatolari ({n})"
        )
        self._s3_fail_toggle.setVisible(n > 0)
        if n == 0:
            self._s3_fail_list.setVisible(False)
            self._s3_retry_btn.setVisible(False)
            self._s3_retry_selected_btn.setVisible(False)
            self._s3_fail_clear_btn.setVisible(False)
        self._s3_fail_list.clear()
        for i, failure in enumerate(self._s3_failures):
            self._s3_fail_list.addItem(
                f"{i + 1}. {failure.item.name}  —  {failure.error}"
            )

    def _on_toggle_s3_failures(self, checked: bool):
        self._s3_fail_list.setVisible(checked)
        self._s3_retry_btn.setVisible(checked)
        self._s3_retry_selected_btn.setVisible(checked)
        self._s3_fail_clear_btn.setVisible(checked)
        self._update_s3_failures_ui()

    def _on_retry_s3_all(self):
        if not self._s3_failures:
            return
        if self._downloader.is_running() or (self._uploader and self._uploader.isRunning()):
            QMessageBox.warning(self, "Band", "Joriy amal yakunlanishini kuting.")
            return
        failures = list(self._s3_failures)
        self._s3_failures.clear()
        self._update_s3_failures_ui()
        for failure in failures:
            failure.item.s3_retry_only = True
            self._queue.append(failure.item)
        self._update_queue_label()
        self._log_panel.append_text(
            f"\nS3 ga qayta yuklash: {len(failures)} ta fayl...\n"
        )
        self._process_next_s3_retry()

    def _on_retry_s3_selected(self):
        rows = sorted(
            {idx.row() for idx in self._s3_fail_list.selectedIndexes()},
            reverse=True,
        )
        if not rows:
            return
        if self._downloader.is_running() or (self._uploader and self._uploader.isRunning()):
            QMessageBox.warning(self, "Band", "Joriy amal yakunlanishini kuting.")
            return
        selected = []
        for row in rows:
            if 0 <= row < len(self._s3_failures):
                selected.append(self._s3_failures.pop(row))
        self._update_s3_failures_ui()
        for failure in reversed(selected):
            failure.item.s3_retry_only = True
            self._queue.append(failure.item)
        self._update_queue_label()
        self._log_panel.append_text(
            f"\nS3 ga qayta yuklash: {len(selected)} ta fayl...\n"
        )
        self._process_next_s3_retry()

    def _process_next_s3_retry(self):
        """Navbatni qayta ishlashni boshlaydi (S3 qayta urinish elementlari uchun)."""
        self._process_next_in_queue()

    def _on_clear_s3_failures(self):
        self._s3_failures.clear()
        self._update_s3_failures_ui()

    def _on_add_to_queue(self):
        item = self._make_queue_item()
        if not item:
            return
        self._queue.append(item)
        self._update_queue_label()
        self._log_panel.append_text(f"Navbatga qo'shildi: {item.name}\n")

    def _on_download(self):
        if self._downloader.is_running():
            QMessageBox.warning(self, "Band", "Yuklash allaqachon bajarilmoqda.")
            return

        # Navbat bo'sh bo'lsa — joriy formani yagona element sifatida qo'shamiz
        if not self._queue:
            item = self._make_queue_item()
            if not item:
                return
            self._queue.append(item)
            self._update_queue_label()

        self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not self._queue:
            self._update_queue_label()
            if self._s3_failures:
                n = len(self._s3_failures)
                self._log_panel.append_text(
                    f"\n--- Navbat yakunlandi. S3 xatolari: {n} ---\n"
                )
                for i, f in enumerate(self._s3_failures, 1):
                    self._log_panel.append_text(
                        f"  {i}. {f.item.name}: {f.error}\n"
                    )
                self._log_panel.append_text(
                    "Qayta urinish uchun «S3 xatolari» bo'limida "
                    "«Barchasini qayta urinish» tugmasini bosing.\n"
                )
                # Xatolar panelini avtomatik ochish
                self._s3_fail_toggle.setChecked(True)
                self._on_toggle_s3_failures(True)
                self._notifier.notify(
                    "Download Helper",
                    f"Navbat yakunlandi. S3 xatolari: {n}",
                    success=False,
                )
            else:
                self._log_panel.append_text("\n--- Navbat yakunlandi ---\n")
                self._notifier.notify("Download Helper", "Yuklab olish navbati yakunlandi")
            return

        item = self._queue.pop(0)
        self._update_queue_label()

        # Faqat S3 yuklashni qayta urinish (fayl allaqachon yuklab olingan)
        if item.s3_retry_only:
            self._current_item = item
            self._log_panel.clear()
            self._full_log.clear()
            self._start_s3_upload(item)
            return

        # Vositalarni tekshirish
        statuses = check_all_tools()
        self._log(format_tool_check_log(statuses))
        missing = [s.name for s in statuses if not s.found]
        if missing:
            self._log(
                f"Yuklab bo'lmaydi. Topilmadi: {', '.join(missing)}\n"
            )
            self._download_btn.setEnabled(True)

            return

        # Bo'sh joyni tekshirish
        if not self._check_disk_space(item.save_dir):
            self._log(f"{item.name} uchun diskda joy yetarli emas. O'tkazib yuborildi.\n")
            self._process_next_in_queue()
            return

        exe = next(s.path for s in statuses if s.name == "N_m3u8DL-RE")

        args = item.parsed.rebuild_command({
            "save_name": item.name,
            "save_dir": item.save_dir,
        })
        args[0] = exe

        # Vazifa yozuvini yaratish
        task = Task(
            name=item.name,
            command=item.raw_command,
            status="Downloading",
            destination_type=item.dest_type,
            destination_path=item.dest_path,
        )
        task = self._task_mgr.create_task(task)
        item.task_id = task.id
        self._current_item = item

        if item.dest_type == "local":
            self._config.set("save_path", item.save_dir)
            self._config.save()
        else:
            self._config.set("s3_default_path", item.dest_path)
            self._config.set_active_s3_profile(item.s3_profile)

        self._log_panel.clear()
        self._full_log.clear()
        self._progress.reset()
        self._stream_lines.clear()
        self._progress.set_status("Yuklanmoqda...")
        self._log(f"Ishga tushirish: {' '.join(args)}\n\n")
        self._download_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._downloader.start(args)

    def _on_stop(self):
        self._cancelling = True

        # Yuklashni to'xtatish
        self._downloader.stop()

        # S3 yuklashni to'xtatish
        if self._uploader and self._uploader.isRunning():
            self._uploader.terminate()
            self._uploader.wait(3000)
            self._uploader = None

        # Joriy vazifaning chala yuklab olingan fayllarini tozalash
        item = self._current_item
        if item:
            self._cleanup_files(item)
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
                self._log("\n--- Bekor qilindi ---\n")
                self._save_task_log(item.task_id)

        # Navbatni tozalash
        self._queue.clear()
        self._current_item = None
        self._update_queue_label()

        self._progress_timer.stop()
        self._download_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.set_finished(False)
        self._progress.set_status("Bekor qilindi")
        if not item or not item.task_id:
            self._log("\n--- Bekor qilindi ---\n")

        self._cancelling = False

    def _cleanup_files(self, item: QueueItem):
        """Vazifaning chala yuklab olingan fayllarini o'chiradi."""
        save_dir = item.save_dir
        if not save_dir or not os.path.isdir(save_dir):
            return

        # Vazifa nomi qatnashgan fayllarni o'chirish
        name_hint = item.name
        for f in os.listdir(save_dir):
            if name_hint and name_hint in f:
                full = os.path.join(save_dir, f)
                if os.path.isfile(full):
                    try:
                        os.remove(full)
                        self._log(f"O'chirildi: {full}\n")
                    except Exception:
                        pass

    def _log(self, text: str):
        """Log panelga va BD ga saqlash uchun to'liq logga yozadi."""
        self._log_panel.append_text(text)
        self._full_log.append(text)

    def _save_task_log(self, task_id: int):
        """To'liq logni ma'lumotlar bazaga saqlaydi."""
        self._task_mgr.save_log(task_id, "".join(self._full_log))

    def _on_download_log(self, text: str):
        """Oddiy log qatori (qator ko'chishi bilan)."""
        self._log_panel.append_text(text)
        self._full_log.append(text)

    def _on_download_progress(self, text: str):
        """Jarayon qatori — oqimlar bo'yicha eslab qolamiz, eng yaxshisini ko'rsatamiz."""
        self._full_log.append(text + "\n")
        self._progress.parse_output(text)

        # Oqimni aniqlash
        stripped = text.strip().lower()
        stream = "unknown"
        for prefix in ("vid", "aud", "sub"):
            if stripped.startswith(prefix):
                stream = prefix
                break
        self._stream_lines[stream] = text

        if not self._progress_timer.isActive():
            self._flush_progress()
            self._progress_timer.start()

    def _flush_progress(self):
        """Loglarda faol (yakunlanmagan) oqimning qatorini ko'rsatadi."""
        if not self._stream_lines:
            return
        # Oqimlar jarayonini progress_panel dan olamiz
        sp = self._progress._stream_progress
        # Faol oqimlar (< 100%), ko'rsatish uchun qatori bor
        active = {s for s, p in sp.items() if p < 100} & set(self._stream_lines)
        pool = active if active else set(self._stream_lines)
        best = max(pool, key=lambda s: self._stream_pri.get(s, 0))
        self._log_panel.replace_last_line(self._stream_lines[best])

    def _on_download_finished(self, exit_code: int):
        self._progress_timer.stop()
        self._flush_progress()

        # Bekor qilish bo'lsa — _on_stop hammasini allaqachon bajargan
        if getattr(self, '_cancelling', False):
            return

        self._stop_btn.setEnabled(False)

        item = self._current_item
        if not item:
            self._download_btn.setEnabled(True)

            return

        if exit_code != 0:
            # Qayta urinish
            if item.retries_left > 0:
                item.retries_left -= 1
                self._log(
                    f"\n--- Xato (kod {exit_code}). "
                    f"Qayta urinish ({item.retries_left} qoldi)... ---\n"
                )
                self._queue.insert(0, item)
                self._current_item = None
                self._process_next_in_queue()
                return

            self._log(f"\n--- Xato (kod {exit_code}) ---\n")
            self._progress.set_finished(False)
            self._notifier.notify(
                "Yuklashda xato", f"{item.name} — kod {exit_code}", success=False
            )
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
                self._save_task_log(item.task_id)
            self._current_item = None
            self._download_btn.setEnabled(True)

            self._process_next_in_queue()
            return

        self._log("\n--- Yuklab olish yakunlandi ---\n")

        if item.dest_type == "s3":
            self._start_s3_upload(item)
        else:
            self._progress.set_finished(True)
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Done")
                self._save_task_log(item.task_id)
            self._current_item = None
            self._download_btn.setEnabled(True)

            self._process_next_in_queue()

    # ── S3 ga yuklash ────────────────────────────────────────────

    def _start_s3_upload(self, item: QueueItem):
        if item.task_id:
            self._task_mgr.update_status(item.task_id, "Uploading")
        self._progress.reset()
        self._progress.set_status("S3 ga yuklanmoqda...")
        self._stop_btn.setEnabled(True)
        self._log("\nS3 ga yuklash boshlanmoqda...\n")

        # Saqlangan yo'l bo'lsa (S3 qayta urinish), shuni ishlatamiz
        local_file = item.local_file or self._find_downloaded_file(item.save_dir, item.name)
        if not local_file or not os.path.isfile(local_file):
            err = "yuklab olingan faylni topib bo'lmadi"
            self._log(f"Xato: {err}.\n")
            self._progress.set_finished(False)
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
            self._s3_failures.append(S3Failure(item=item, error=err))
            self._update_s3_failures_ui()
            self._current_item = None
            self._download_btn.setEnabled(True)

            self._process_next_in_queue()
            return
        item.local_file = local_file

        s3_config = self._config.get_s3_config(item.s3_profile)
        if not s3_config:
            self._log(f"Xato: «{item.s3_profile}» S3 profili topilmadi.\n")
            self._progress.set_finished(False)
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
            self._current_item = None
            self._download_btn.setEnabled(True)

            self._process_next_in_queue()
            return

        s3_path = item.dest_path or f"/{item.name}"

        self._log(f"S3 profili: {item.s3_profile}\n")

        self._uploader = S3Uploader(
            local_file, s3_path, s3_config,
            delete_local=item.delete_local,
            parent=self,
        )
        self._uploader.progress.connect(self._progress.set_progress)
        self._uploader.progress_info.connect(self._progress.set_info)
        self._uploader.log_message.connect(self._on_upload_log)
        self._uploader.upload_finished.connect(self._on_upload_finished)
        self._uploader.start()

    def _find_downloaded_file(self, directory: str, name_hint: str) -> str | None:
        if not directory or not os.path.isdir(directory):
            return None
        files = []
        for f in os.listdir(directory):
            full = os.path.join(directory, f)
            if os.path.isfile(full):
                files.append(full)
        if not files:
            return None
        for f in files:
            if name_hint in os.path.basename(f):
                return f
        return max(files, key=os.path.getsize)

    def _on_upload_log(self, text: str):
        self._log(text)

    def _on_upload_finished(self, success: bool, message: str):
        item = self._current_item
        if item and item.task_id:
            self._task_mgr.update_status(item.task_id, "Done" if success else "Failed")
            self._save_task_log(item.task_id)
        if not success and item:
            self._s3_failures.append(S3Failure(item=item, error=message))
            self._update_s3_failures_ui()
            self._notifier.notify(
                "S3 xatosi", f"{item.name} — {message}", success=False
            )
        self._progress.set_finished(success)
        self._current_item = None
        self._uploader = None
        self._download_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

        self._process_next_in_queue()

    # ── Bo'sh joyni tekshirish ───────────────────────────────────

    @staticmethod
    def _check_disk_space(path: str, min_mb: int = 500) -> bool:
        """Kamida min_mb MB bo'sh joy borligini tekshiradi."""
        try:
            target = path
            while not os.path.exists(target):
                target = os.path.dirname(target)
                if not target:
                    return True
            usage = shutil.disk_usage(target)
            free_mb = usage.free / (1024 * 1024)
            return free_mb >= min_mb
        except OSError:
            return True

    # ── «Tarix» varag'i slotlari ─────────────────────────────────

    def _on_tab_changed(self, index: int):
        if index == 1:
            self._refresh_history()

    def _refresh_history(self):
        tasks = self._task_mgr.get_all_tasks()
        self._task_list.load_tasks(tasks)

    def _on_view_task_logs(self, task_id: int):
        log = self._task_mgr.get_log(task_id)
        self._history_log.clear()
        self._history_log.appendPlainText(log)

    def _on_redownload(self, task_id: int):
        task = self._task_mgr.get_task(task_id)
        if not task:
            return
        self._tabs.setCurrentIndex(0)
        self._cmd_input.set_text(task.command)
        self._file_name.set_name(task.name)
        self._on_parse()

    def _on_delete_task(self, task_id: int):
        reply = QMessageBox.question(
            self, "Vazifani o'chirish", "Bu vazifa tarixdan o'chirilsinmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._task_mgr.delete_task(task_id)
            self._refresh_history()
            self._history_log.clear()

    # ── Loglarni nusxalash / saqlash ─────────────────────────────

    def _copy_log(self, panel: LogPanel):
        text = panel.toPlainText()
        if not text.strip():
            return
        self._ignore_clipboard = True
        QApplication.clipboard().setText(text)
        QTimer.singleShot(100, lambda: setattr(self, '_ignore_clipboard', False))

    def _save_log(self, panel: LogPanel):
        text = panel.toPlainText()
        if not text.strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Logni saqlash", "log.txt", "Matn fayllar (*.txt);;Barcha fayllar (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def closeEvent(self, event):
        self._notifier.cleanup()
        super().closeEvent(event)
