"""Asosiy oyna: interfeys HTML/CSS/JS (QWebEngineView), mantiq Python da.

- UI fayllari: ``app/web/`` (index.html, style.css, app.js, progressbar.html)
- JS <-> Python aloqasi: QWebChannel (obek nomi ``dh``)
- Barcha yuklab olish / navbat / S3 / tarix mantiqlari shu oynada saqlanadi;
  widget o'rniga JS ga ``window.DH.call(...)`` orqali hodisalarni yuboramiz.
"""

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QApplication,
)

from app.core.command_parser import parse_command, ParsedCommand
from app.core.normalizer import normalize_filename
from app.core.config import ConfigManager
from app.core.task_manager import TaskManager, Task
from app.core.downloader import (
    Downloader, check_all_tools, format_tool_check_log,
)
from app.core.s3_uploader import S3Uploader
from app.core.notifier import Notifier
from app.dialogs.s3_config_dialog import S3ConfigDialog
from app.dialogs.help_dialog import HelpDialog


def _error_log_path() -> str:
    """Exe yonidagi xato kundaligi faylining yo'li."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "DownloadHelper-error.log")


def web_root() -> Path:
    """UI fayllari papkasi (sozlangan va sozlanmagan holatlar uchun)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "web"
    return Path(__file__).resolve().parent / "web"


# ── N_m3u8DL-RE jarayon qatorini tahlil qilish uchun regexlar ──
_STREAM_RE = re.compile(r"^(Vid|Aud|Sub)\b", re.IGNORECASE)
_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)%")
_FRACTION_RE = re.compile(r"(\d+)/(\d+)")
_SPEED_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*(?:Ki?B|Mi?B|Gi?B|[KMG]?B|B)(?:ps|/s))", re.IGNORECASE
)
_TIME_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")
_STREAM_PRIORITY = {"vid": 3, "aud": 2, "sub": 1}


def parse_progress_line(text: str, stream_progress: dict[str, int]) -> dict:
    """N_m3u8DL-RE jarayon qatorini tahlil qiladi (toza funksiya, test qilinadi).

    ``stream_progress`` o'rniga yozadi: {oqim: foiz}.
    Qaytaradi progress holati o'zgarishlari:
    ``{"pct": int|None, "info": str|None, "status": str|None}``
    """
    changes: dict = {"pct": None, "info": None, "status": None}

    pct = -1
    pct_match = _PCT_RE.search(text)
    if pct_match:
        pct = int(float(pct_match.group(1)))
    else:
        frac = _FRACTION_RE.search(text)
        if frac:
            done, total = int(frac.group(1)), int(frac.group(2))
            if total > 0:
                pct = int(done * 100 / total)

    if pct >= 0:
        stream_match = _STREAM_RE.match(text.strip())
        stream = stream_match.group(1).lower() if stream_match else "unknown"
        stream_progress[stream] = pct
        changes["pct"] = primary_progress(stream_progress)

    info_parts = []
    speed_match = _SPEED_RE.search(text)
    if speed_match:
        info_parts.append(f"Tezlik: {speed_match.group(1)}")
    time_matches = _TIME_RE.findall(text)
    if time_matches:
        info_parts.append(f"Qoldi: {time_matches[-1]}")
    if info_parts:
        changes["info"] = "  |  ".join(info_parts)
    elif not pct_match:
        changes["status"] = text.strip()

    return changes


def primary_progress(stream_progress: dict[str, int]) -> int:
    """Faol oqimning (hali 100% bo'lmagan) jarayonini qaytaradi.

    Agar hali yuklanayotgan (<100%) oqimlar bo'lsa, ulardan eng yuqori
    prioritetlisini (vid > aud > sub) ko'rsatadi; barchasi 100% bo'lsa — 100.
    """
    if not stream_progress:
        return 0
    active = {s: p for s, p in stream_progress.items() if p < 100}
    if not active:
        return 100
    best_stream = max(active, key=lambda s: _STREAM_PRIORITY.get(s, 0))
    return active[best_stream]


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


class WebBridge(QObject):
    """JS -> Python kanal (QWebChannel da ``dh`` nomi bilan ro'yxatdan o'tadi)."""

    def __init__(self, window: "MainWindow"):
        super().__init__()
        self._w = window

    def _safe(self, fn, *args):
        """Slot'dan chaqirilgan amalni bajaradi; xatolarni xato kundaligiga yozadi."""
        try:
            fn(*args)
        except Exception:
            import traceback
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            try:
                with open(_error_log_path(), "a", encoding="utf-8") as f:
                    f.write(tb + "\n" + "=" * 60 + "\n")
            except Exception:
                pass

    # ── Hayot sikli / holat ──
    @Slot()
    def loaded(self):
        self._safe(self._w._on_ui_loaded)

    @Slot(int)
    def tabChanged(self, index: int):
        self._safe(self._w._on_tab_changed, int(index))

    # ── Forma sinxroni (JS -> Python) ──
    @Slot(str)
    def commandSet(self, text: str):
        self._w._form["command"] = text or ""

    @Slot(str)
    def nameSet(self, text: str):
        self._w._form["name"] = text or ""

    @Slot(str)
    def localPathSet(self, text: str):
        self._w._form["local_path"] = text or ""

    @Slot(str)
    def s3PathSet(self, text: str):
        self._w._form["s3_path"] = text or ""

    @Slot(str)
    def destSet(self, dest: str):
        self._w._form["dest"] = "s3" if dest == "s3" else "local"

    @Slot(bool)
    def deleteLocalSet(self, checked: bool):
        self._w._form["delete_local"] = bool(checked)

    @Slot(bool)
    def autoSet(self, checked: bool):
        self._w._form["auto"] = bool(checked)
        if checked:
            dest = "S3" if self._w._form["dest"] == "s3" else "Lokal"
            self._safe(self._w._log, f"Avto-rejim yoqildi. Buyruqni nusxalang va «Joylash» tugmasini bosing. Manzil: {dest}.\n")
        else:
            self._safe(self._w._log, "Avto-rejim o'chirildi.\n")

    @Slot(bool)
    def autoNormalizeSet(self, checked: bool):
        self._w._form["auto_normalize"] = bool(checked)

    @Slot(str)
    def s3ProfileSet(self, name: str):
        self._w._form["s3_profile"] = name or ""

    @Slot(int)
    def retrySet(self, n: int):
        self._w._form["retry"] = max(1, min(10, int(n)))

    # ── Amallar (JS -> Python) ──
    @Slot()
    def parse(self):
        self._safe(self._w._on_parse)

    @Slot(str)
    def pasted(self, text: str):
        """Textarea'da paste bo'ldi — matn ayni damda beriladi."""
        self._w._form["command"] = text or ""
        if (text or "").strip():
            self._safe(self._w._on_parse)

    @Slot()
    def paste(self):
        self._safe(self._w._on_paste_command)

    @Slot()
    def normalize(self):
        self._safe(self._w._on_normalize)

    @Slot()
    def refreshTools(self):
        self._safe(self._w._refresh_tools_status)

    @Slot()
    def browseLocal(self):
        self._safe(self._w._on_browse_local)

    @Slot()
    def s3Settings(self):
        self._safe(self._w._on_s3_settings)

    @Slot()
    def help(self):
        self._safe(self._w._on_help)

    @Slot()
    def autoHelp(self):
        self._safe(self._w._on_auto_help)

    @Slot()
    def download(self):
        self._safe(self._w._on_download)

    @Slot()
    def addQueue(self):
        self._safe(self._w._on_add_to_queue)

    @Slot()
    def stop(self):
        self._safe(self._w._on_stop)

    @Slot()
    def clearForm(self):
        self._safe(self._w._on_clear_form)

    @Slot()
    def openFolder(self):
        self._safe(self._w._on_open_output_folder)

    @Slot(list)
    def queueRemove(self, indexes):
        self._safe(self._w._on_remove_from_queue, [int(i) for i in indexes])

    @Slot()
    def queueClear(self):
        self._safe(self._w._on_clear_queue)

    @Slot()
    def s3RetryAll(self):
        self._safe(self._w._on_retry_s3_all)

    @Slot(list)
    def s3RetrySelected(self, indexes):
        self._safe(self._w._on_retry_s3_selected, [int(i) for i in indexes])

    @Slot()
    def s3FailClear(self):
        self._safe(self._w._on_clear_s3_failures)

    @Slot(str)
    def logCopy(self, text: str):
        if (text or "").strip():
            QApplication.clipboard().setText(text)

    @Slot(str)
    def logSave(self, text: str):
        self._safe(self._w._on_save_log_text, text)

    @Slot(str)
    def histLogCopy(self, text: str):
        if (text or "").strip():
            QApplication.clipboard().setText(text)

    @Slot(str)
    def histLogSave(self, text: str):
        self._safe(self._w._on_save_log_text, text)

    @Slot(int)
    def viewTaskLogs(self, task_id: int):
        self._safe(self._w._on_view_task_logs, int(task_id))

    @Slot(int)
    def redownloadTask(self, task_id: int):
        self._safe(self._w._on_redownload, int(task_id))

    @Slot(int)
    def deleteTask(self, task_id: int):
        self._safe(self._w._on_delete_task, int(task_id))

    @Slot(str)
    def openUrl(self, url: str):
        QDesktopServices.openUrl(QUrl(url))


class MainWindow(QMainWindow):
    """Asosiy oyna — HTML interfeys + Python mantiqi."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yuklab olish yordamchisi")
        self.setMinimumSize(700, 600)
        self.resize(1010, 880)

        # ── Yadro ──
        self._config = ConfigManager()
        self._task_mgr = TaskManager()
        self._downloader = Downloader(self)
        self._notifier = Notifier()
        self._notifier.set_window(self)
        self._uploader: S3Uploader | None = None
        self._cancelling = False
        self._current_item: QueueItem | None = None
        self._queue: list[QueueItem] = []
        self._s3_failures: list[S3Failure] = []
        self._parsed: ParsedCommand | None = None
        self._last_output_dir = ""

        # ── Forma holati (yagona manba — Python) ──
        self._form: dict = {
            "command": "",
            "name": "",
            "dest": "local",
            "local_path": self._config.get("save_path") or "",
            "s3_profile": self._config.get_active_s3_profile(),
            "s3_path": self._config.get("s3_default_path") or "",
            "delete_local": True,
            "auto": False,
            "auto_normalize": True,
            "retry": 2,
        }

        # ── Progress / log holati ──
        self._stream_progress: dict[str, int] = {}
        self._stream_lines: dict[str, str] = {}
        self._full_log: list[str] = []

        self._progress_state: dict = {}
        self._last_replaced_line = ""
        self._progress_flush_timer = QTimer(self)
        self._progress_flush_timer.setInterval(100)
        self._progress_flush_timer.setSingleShot(True)
        self._progress_flush_timer.timeout.connect(self._flush_progress_ui)

        self._logline_timer = QTimer(self)
        self._logline_timer.setInterval(200)
        self._logline_timer.setSingleShot(True)
        self._logline_timer.timeout.connect(self._flush_log_line)

        # ── Web ko'rinish ──
        web_dir = web_root()
        if not (web_dir / "index.html").is_file():
            QMessageBox.critical(
                self, "Xato",
                f"UI fayllari topilmadi:\n{web_dir}\n\n"
                "Ilova papkasidagi «web» papkasini tekshiring.",
            )
        self._view = self._create_web_view()
        self.setCentralWidget(self._view)
        self._bridge = WebBridge(self)
        from PySide6.QtWebChannel import QWebChannel
        channel = QWebChannel()
        channel.registerObject("dh", self._bridge)
        self._view.page().setWebChannel(channel)
        self._view.load(QUrl.fromLocalFile(str(web_dir / "index.html")))

        # ── Signallar ──
        self._downloader.log_received.connect(self._on_download_log)
        self._downloader.progress_received.connect(self._on_download_progress)
        self._downloader.finished.connect(self._on_download_finished)

        self._ui_ready = False

    def _create_web_view(self):
        """QWebEngineView yaratadi (lazy import — WebEngine'siz muhitda ham
        modul import bo'ladi, faqat oyna yaratilganda paket kerak)."""
        from PySide6.QtCore import Qt
        from PySide6.QtWebEngineWidgets import QWebEngineView

        view = QWebEngineView(self)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        view.loadFinished.connect(self._on_load_finished)
        return view

    def _on_load_finished(self, ok: bool):
        if not ok:
            QMessageBox.critical(self, "Xato", "Interfeys yuklanmadi (index.html).")

    # ── Python -> JS yordamchilar ──────────────────────────

    def _js(self, name: str, *args):
        """JS da ``window.DH.call(name, args)`` chaqiradi."""
        if not self._ui_ready:
            return
        payload = json.dumps(list(args), ensure_ascii=False)
        self._view.page().runJavaScript(f"window.DH.call({json.dumps(name)}, {payload})")

    def _prog(self, **changes):
        """Progress holatini to'playdi va 100 ms da bir marta yuboradi."""
        self._progress_state.update(changes)
        if not self._progress_flush_timer.isActive():
            self._progress_flush_timer.start()

    def _flush_progress_ui(self):
        if self._progress_state:
            self._js("progress", dict(self._progress_state))
            self._progress_state.clear()

    def _log(self, text: str):
        """Log panelga va BD ga saqlash uchun to'liq logga yozadi."""
        self._js("logAppend", text)
        self._full_log.append(text)

    def _hist_log(self, text: str):
        self._js("histLogAppend", text)

    def _set_busy(self, *, download=True, stop=False, clear=True, folder=False):
        self._js("busy", download, stop, clear, folder)

    def _set_open_folder_enabled(self, enabled: bool):
        d = not self._downloader.is_running()
        s = not d
        c = d
        self._js("busy", d, s, c, enabled)

    # ── UI tayyor bo'lgani ─────────────────────────────────

    def _on_ui_loaded(self):
        self._ui_ready = True
        self._js("init", dict(self._form))
        self._js("s3Profiles", self._config.get_s3_profile_names(), self._form["s3_profile"])
        self._js("toolsStatusUpdate", self._tools_payload())
        self._js("queueUpdate", self._queue_payload())
        self._js("s3FailuresUpdate", self._s3_payload())
        self._js("tasksUpdate", self._tasks_payload())
        d = not self._downloader.is_running()
        self._set_busy(
            download=d, stop=not d, clear=d,
            folder=bool(self._last_output_dir and os.path.isdir(self._last_output_dir)),
        )

    # ── Ma'lumot to'plamlari (Python -> JS) ────────────────

    def _tools_payload(self):
        return [
            {"name": s.name, "found": bool(s.found), "path": s.path or ""}
            for s in check_all_tools()
        ]

    def _queue_payload(self):
        return [
            {"name": item.name, "dest": item.dest_type.upper()}
            for item in self._queue
        ]

    def _s3_payload(self):
        return [
            {"name": f.item.name, "error": f.error} for f in self._s3_failures
        ]

    def _tasks_payload(self):
        out = []
        for t in self._task_mgr.get_all_tasks():
            out.append({
                "id": t.id,
                "name": t.name,
                "status": t.status,
                "date": (t.created_at or "").split(" ")[0],
                "dest": "S3" if t.destination_type == "s3" else "Lokal",
            })
        return out

    # ── Vositalar holati ───────────────────────────────────

    def _refresh_tools_status(self):
        """Yordamchi executable fayllar topilganini UI'da ko'rsatadi."""
        statuses = check_all_tools()
        self._js("toolsStatusUpdate", [
            {"name": s.name, "found": bool(s.found), "path": s.path or ""}
            for s in statuses
        ])
        return statuses

    # ── Slotlar ────────────────────────────────────────────

    def _on_tab_changed(self, index: int):
        if index == 1:
            self._js("tasksUpdate", self._tasks_payload())

    def _on_parse(self):
        raw = self._form["command"].strip()
        if not raw:
            return
        self._parsed = parse_command(raw)
        if self._parsed.save_name:
            self._form["name"] = self._parsed.save_name
            self._js("init", {"name": self._form["name"]})
        if self._parsed.url:
            self._log(f"URL: {self._parsed.url}\n")
        if self._parsed.save_name:
            self._log(f"Nomi: {self._parsed.save_name}\n")

    def _on_paste_command(self):
        """«Joylash» tugmasi: Ctrl+V kabi buferdagi matnni maydonga qo'yadi."""
        text = QApplication.clipboard().text()
        if not text:
            return
        self._form["command"] = text
        self._js("init", {"command": text})
        if self._form["auto"]:
            # JS da input hodisasi kutmaymiz — to'g'ridan-to'g'ri davom etamiz.
            QTimer.singleShot(0, self._run_auto_mode_for_current_command)

    def _on_normalize(self):
        name = self._form["name"].strip()
        if name:
            new = normalize_filename(name)
            self._form["name"] = new
            self._js("init", {"name": new})

    def _on_browse_local(self):
        path = QFileDialog.getExistingDirectory(self, "Yuklab olish uchun papkani tanlang")
        if path:
            self._form["local_path"] = path
            self._js("init", {"local_path": path})

    def _on_s3_settings(self):
        dlg = S3ConfigDialog(self._config, self)
        dlg.exec()
        names = self._config.get_s3_profile_names()
        active = self._config.get_active_s3_profile()
        if active and active not in names:
            active = ""
        if not self._form.get("s3_profile") or self._form.get("s3_profile") not in names:
            self._form["s3_profile"] = active
        self._js("s3Profiles", names, self._form.get("s3_profile") or active)
        self._js("init", {"s3_profile": self._form.get("s3_profile") or ""})

    def _on_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _on_auto_help(self):
        QMessageBox.information(self, "Avto-rejim", (
            "<b>Avto-rejim qanday ishlaydi:</b><br><br>"
            "1. «Avto-rejim» belgilash qutisini yoqing<br>"
            "2. Saqlash joyini sozlang (Lokal yoki S3, yo'l, profil)<br>"
            "3. N_m3u8DL-RE buyrug'ini istalgan joydan nusxalang (Ctrl+C)<br>"
            "4. «Joylash» tugmasini bosing<br>"
            "5. Dastur avtomatik ravishda:<br>"
            "&nbsp;&nbsp;— buyruqni tahlil qiladi<br>"
            "&nbsp;&nbsp;— fayl nomini normallashtiradi (yoqilgan bo'lsa)<br>"
            "&nbsp;&nbsp;— yuklashni boshlaydi yoki navbatga qo'shadi<br><br>"
            "<b>Joylash:</b> almashinuv buferidagi matnni buyruq maydoniga "
            "Ctrl+V kabi qo'yadi. Dastur buferni o'zi doimiy kuzatmaydi.<br><br>"
            "<b>Nomni avto-normallashtirish:</b> kirillni lotinchaga "
            "o'giradi, probellarni «_» ga almashtiradi, maxsus "
            "belgilarni olib tashlaydi.<br><br>"
            "<b>Saqlash joyi:</b> joriy sozlamalar ishlatiladi "
            "(Lokal/S3, yo'l, profil). Ularni avto-rejimni yoqishdan "
            "oldin yoki istalgan vaqtda o'zgartiring."
        ))

    # ── Avto-rejim («Joylash» orqali) ──────────────────────

    def _run_auto_mode_for_current_command(self):
        """«Joylash» orqali qo'yilgan buyruq uchun avto-rejim amallarini bajaradi."""
        text = self._form["command"].strip()
        if not text:
            return
        if "N_m3u8DL-RE" not in text and "n_m3u8dl-re" not in text.lower():
            self._log("Avto-rejim: buferda N_m3u8DL-RE buyrug'i topilmadi.\n")
            return

        self._js("showTab", 0)
        # Joylash signalidan keyin ham aniq joriy buyruqni tahlil qilamiz.
        self._parsed = parse_command(text)
        if not self._parsed.url:
            self._log("Avto-rejim: buyruqni tahlil qilib bo'lmadi\n")
            self._notifier.notify("Avto-rejim", "Buyruqni tahlil qilib bo'lmadi", success=False)
            return

        if self._form["auto_normalize"]:
            self._on_normalize()

        name = self._form["name"].strip() or "output"
        dest = "S3" if self._form["dest"] == "s3" else "Lokal"
        self._log(f"Avto-rejim: {name} → {dest}\n")

        # Yuklash ketayotgan bo'lsa — navbatga qo'shamiz, aks holda darhol yuklaymiz.
        if self._downloader.is_running():
            self._on_add_to_queue()
            self._notifier.notify("Navbatga", f"{name} → {dest}")
        else:
            self._on_download()
            self._notifier.notify("Yuklab olish", f"{name} → {dest}")

    # ── Navbat elementini yaratish ─────────────────────────

    def _make_queue_item(self) -> QueueItem | None:
        """Formaning joriy holatidan QueueItem yig'adi. Xato bo'lsa None qaytaradi."""
        raw_cmd = self._form["command"].strip()
        if not raw_cmd:
            QMessageBox.warning(self, "Xato", "Buyruqni qo'ying.")
            return None

        if not self._parsed:
            self._parsed = parse_command(raw_cmd)

        name = self._form["name"].strip() or self._parsed.save_name or "output"
        is_local = self._form["dest"] == "local"

        save_dir = self._form["local_path"].strip()
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
            s3_raw = self._form["s3_path"].strip()
            # Agar yo'l papka bo'lsa (oxirgi bo'lakda kengaytma yo'q bo'lsa),
            # fayl nomini avtomatik qo'shamiz
            last_segment = s3_raw.rstrip("/").rsplit("/", 1)[-1] if s3_raw else ""
            if not last_segment or "." not in last_segment:
                file_with_ext = name if "." in name else name + ".mp4"
                dest_path = s3_raw.rstrip("/") + "/" + file_with_ext
            else:
                dest_path = s3_raw
        delete_local = (not is_local) and self._form["delete_local"]
        s3_profile = "" if is_local else self._form.get("s3_profile", "")

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
            retries_left=self._form.get("retry", 2),
        )

    # ── Vazifalar navbati ──────────────────────────────────

    def _update_queue_ui(self):
        self._js("queueUpdate", self._queue_payload())

    def _on_remove_from_queue(self, indexes: list[int]):
        for row in sorted(set(indexes), reverse=True):
            if 0 <= row < len(self._queue):
                removed = self._queue.pop(row)
                self._log(f"Navbatdan o'chirildi: {removed.name}\n")
        self._update_queue_ui()

    def _on_clear_queue(self):
        if not self._queue:
            return
        self._queue.clear()
        self._log("Navbat tozalandi.\n")
        self._update_queue_ui()

    # ── S3 xatolari paneli ─────────────────────────────────

    def _update_s3_failures_ui(self):
        self._js("s3FailuresUpdate", self._s3_payload())

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
        self._update_queue_ui()
        self._log(f"\nS3 ga qayta yuklash: {len(failures)} ta fayl...\n")
        self._process_next_in_queue()

    def _on_retry_s3_selected(self, indexes: list[int]):
        if not indexes:
            return
        if self._downloader.is_running() or (self._uploader and self._uploader.isRunning()):
            QMessageBox.warning(self, "Band", "Joriy amal yakunlanishini kuting.")
            return
        selected = []
        for row in sorted(set(indexes), reverse=True):
            if 0 <= row < len(self._s3_failures):
                selected.append(self._s3_failures.pop(row))
        self._update_s3_failures_ui()
        for failure in reversed(selected):
            failure.item.s3_retry_only = True
            self._queue.append(failure.item)
        self._update_queue_ui()
        self._log(f"\nS3 ga qayta yuklash: {len(selected)} ta fayl...\n")
        self._process_next_in_queue()

    def _on_clear_s3_failures(self):
        self._s3_failures.clear()
        self._update_s3_failures_ui()

    def _on_add_to_queue(self):
        item = self._make_queue_item()
        if not item:
            return
        self._queue.append(item)
        self._update_queue_ui()
        self._log(f"Navbatga qo'shildi: {item.name}\n")

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
            self._update_queue_ui()

        self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not self._queue:
            self._update_queue_ui()
            if self._s3_failures:
                n = len(self._s3_failures)
                self._log(f"\n--- Navbat yakunlandi. S3 xatolari: {n} ---\n")
                for i, f in enumerate(self._s3_failures, 1):
                    self._log(f"  {i}. {f.item.name}: {f.error}\n")
                self._log(
                    "Qayta urinish uchun «S3 xatolari» bo'limida "
                    "«Barchasini qayta urinish» tugmasini bosing.\n"
                )
                # Xatolar panelini avtomatik ochish
                self._js("s3FailuresOpen")
                self._notifier.notify(
                    "Download Helper",
                    f"Navbat yakunlandi. S3 xatolari: {n}",
                    success=False,
                )
            else:
                self._log("\n--- Navbat yakunlandi ---\n")
                self._notifier.notify("Download Helper", "Yuklab olish navbati yakunlandi")
            return

        item = self._queue.pop(0)
        self._update_queue_ui()

        # Faqat S3 yuklashni qayta urinish (fayl allaqachon yuklab olingan)
        if item.s3_retry_only:
            self._current_item = item
            self._js("logClear")
            self._full_log.clear()
            self._start_s3_upload(item)
            return

        # Vositalarni tekshirish va holat panelini yangilash
        statuses = self._refresh_tools_status()
        self._log(format_tool_check_log(statuses))
        missing = [s.name for s in statuses if not s.found]
        if missing:
            self._log(f"Yuklab bo'lmaydi. Topilmadi: {', '.join(missing)}\n")
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
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

        self._js("logClear")
        self._full_log.clear()
        self._last_replaced_line = ""
        self._js("progress", {"reset": True})
        self._stream_lines.clear()
        self._stream_progress.clear()
        self._prog(status="Yuklanmoqda...")
        self._log(f"Ishga tushirish: {' '.join(args)}\n\n")
        self._set_busy(download=False, stop=True, clear=False,
                       folder=self._open_folder_enabled())
        self._downloader.start(args)

    def _open_folder_enabled(self) -> bool:
        return bool(self._last_output_dir and os.path.isdir(self._last_output_dir))

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
        self._update_queue_ui()

        self._logline_timer.stop()
        self._set_busy(download=True, stop=False, clear=True,
                       folder=self._open_folder_enabled())
        self._prog(finished=False, status="Bekor qilindi")
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

    # ── Log ────────────────────────────────────────────────

    def _flush_log_line(self):
        """Loglarda faol (yakunlanmagan) oqimning qatorini ko'rsatadi."""
        if not self._stream_lines:
            return
        active = {s for s, p in self._stream_progress.items() if p < 100} & set(self._stream_lines)
        pool = active if active else set(self._stream_lines)
        best = max(pool, key=lambda s: _STREAM_PRIORITY.get(s, 0))
        line = self._stream_lines[best]
        if line == self._last_replaced_line:
            return
        self._last_replaced_line = line
        self._js("logReplaceLast", line)

    def _on_download_log(self, text: str):
        """Oddiy log qatori."""
        self._log(text)

    def _on_download_progress(self, text: str):
        """Jarayon qatori — oqimlar bo'yicha eslab qolamiz, eng yaxshisini ko'rsatamiz."""
        self._full_log.append(text + "\n")
        self._parse_progress_line(text)

        stripped = text.strip().lower()
        stream = "unknown"
        for prefix in ("vid", "aud", "sub"):
            if stripped.startswith(prefix):
                stream = prefix
                break
        self._stream_lines[stream] = text

        if not self._logline_timer.isActive():
            self._logline_timer.start()

    def _parse_progress_line(self, text: str):
        """N_m3u8DL-RE jarayon qatorini tahlil qilib progress holatini yangilaydi."""
        changes = parse_progress_line(text, self._stream_progress)
        if changes["pct"] is not None:
            self._prog(pct=changes["pct"])
        if changes["info"] is not None:
            self._prog(info=changes["info"])
        if changes["status"] is not None:
            self._prog(status=changes["status"])

    def _save_task_log(self, task_id: int):
        """To'liq logni ma'lumotlar bazaga saqlaydi."""
        self._task_mgr.save_log(task_id, "".join(self._full_log))

    def _on_download_finished(self, exit_code: int):
        self._logline_timer.stop()
        self._flush_log_line()

        # Bekor qilish bo'lsa — _on_stop hammasini allaqachon bajargan
        if getattr(self, "_cancelling", False):
            return

        item = self._current_item
        if not item:
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
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
            self._prog(finished=False, status="Xato")
            self._notifier.notify(
                "Yuklashda xato", f"{item.name} — kod {exit_code}", success=False
            )
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
                self._save_task_log(item.task_id)
            self._current_item = None
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
            self._process_next_in_queue()
            return

        self._log("\n--- Yuklab olish yakunlandi ---\n")

        if item.dest_type == "s3":
            self._start_s3_upload(item)
        else:
            self._prog(finished=True, status="Tayyor", info="")
            self._set_last_output_directory(item.save_dir)
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Done")
                self._save_task_log(item.task_id)
            self._current_item = None
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
            self._process_next_in_queue()

    # ── S3 ga yuklash ──────────────────────────────────────

    def _start_s3_upload(self, item: QueueItem):
        if item.task_id:
            self._task_mgr.update_status(item.task_id, "Uploading")
        self._js("progress", {"reset": True})
        self._stream_progress.clear()
        self._prog(status="S3 ga yuklanmoqda...")
        self._set_busy(download=False, stop=True, clear=False,
                       folder=self._open_folder_enabled())
        self._log("\nS3 ga yuklash boshlanmoqda...\n")

        # Saqlangan yo'l bo'lsa (S3 qayta urinish), shuni ishlatamiz
        local_file = item.local_file or self._find_downloaded_file(item.save_dir, item.name)
        if not local_file or not os.path.isfile(local_file):
            err = "yuklab olingan faylni topib bo'lmadi"
            self._log(f"Xato: {err}.\n")
            self._prog(finished=False, status="Xato")
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
            self._s3_failures.append(S3Failure(item=item, error=err))
            self._update_s3_failures_ui()
            self._current_item = None
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
            self._process_next_in_queue()
            return
        item.local_file = local_file

        s3_config = self._config.get_s3_config(item.s3_profile)
        if not s3_config:
            self._log(f"Xato: «{item.s3_profile}» S3 profili topilmadi.\n")
            self._prog(finished=False, status="Xato")
            if item.task_id:
                self._task_mgr.update_status(item.task_id, "Failed")
            self._current_item = None
            self._set_busy(download=True, stop=False, clear=True,
                           folder=self._open_folder_enabled())
            self._process_next_in_queue()
            return

        s3_path = item.dest_path or f"/{item.name}"

        self._log(f"S3 profili: {item.s3_profile}\n")

        self._uploader = S3Uploader(
            local_file, s3_path, s3_config,
            delete_local=item.delete_local,
            parent=self,
        )
        self._uploader.progress.connect(lambda v: self._prog(pct=min(int(v), 100)))
        self._uploader.progress_info.connect(lambda t: self._prog(info=t))
        self._uploader.log_message.connect(self._log)
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
        self._prog(finished=success, status="Tayyor" if success else "Xato")
        if success and item:
            self._set_last_output_directory(item.save_dir)
        self._current_item = None
        self._uploader = None
        self._set_busy(download=True, stop=False, clear=True,
                       folder=self._open_folder_enabled())
        self._process_next_in_queue()

    # ── Bo'sh joyni tekshirish ─────────────────────────────

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

    def _set_last_output_directory(self, directory: str):
        """Oxirgi muvaffaqiyatli yuklash papkasini eslab qoladi."""
        if directory and os.path.isdir(directory):
            self._last_output_dir = directory
            d = not self._downloader.is_running()
            self._js("busy", d, not d, d, True)

    def _on_open_output_folder(self):
        """Oxirgi tayyor fayl joylashgan lokal papkani tizim fayl oynasida ochadi."""
        if not self._last_output_dir or not os.path.isdir(self._last_output_dir):
            QMessageBox.information(
                self,
                "Papka topilmadi",
                "Avval muvaffaqiyatli yuklashni yakunlang.",
            )
            return
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_output_dir))
        if not opened:
            QMessageBox.warning(self, "Xato", "Papka oynasini ochib bo'lmadi.")

    # ── Forma tozalash ─────────────────────────────────────

    def _on_clear_form(self):
        """Yangi vazifa uchun joriy forma ma'lumotlarini tozalaydi."""
        if self._downloader.is_running() or (self._uploader and self._uploader.isRunning()):
            return
        self._form["command"] = ""
        self._form["name"] = ""
        self._parsed = None
        self._logline_timer.stop()
        self._stream_lines.clear()
        self._stream_progress.clear()
        self._full_log.clear()
        self._js("init", {"command": "", "name": ""})
        self._js("focusCommand")
        self._js("progress", {"reset": True})
        self._js("logClear")
        self._last_replaced_line = ""

    # ── Loglarni saqlash ───────────────────────────────────

    def _on_save_log_text(self, text: str):
        if not (text or "").strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Logni saqlash", "log.txt", "Matn fayllar (*.txt);;Barcha fayllar (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    # ── «Tarix» varag'i slotlari ───────────────────────────

    def _on_view_task_logs(self, task_id: int):
        log = self._task_mgr.get_log(task_id)
        self._js("histLogClear")
        if log:
            self._js("histLogAppend", log)

    def _on_redownload(self, task_id: int):
        task = self._task_mgr.get_task(task_id)
        if not task:
            return
        self._form["command"] = task.command
        self._form["name"] = task.name
        self._js("showTab", 0)
        self._js("init", {"command": task.command, "name": task.name})
        self._on_parse()

    def _on_delete_task(self, task_id: int):
        reply = QMessageBox.question(
            self, "Vazifani o'chirish", "Bu vazifa tarixdan o'chirilsinmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._task_mgr.delete_task(task_id)
            self._js("tasksUpdate", self._tasks_payload())
            self._js("histLogClear")

    def closeEvent(self, event):
        self._logline_timer.stop()
        self._progress_flush_timer.stop()
        self._notifier.cleanup()
        super().closeEvent(event)
