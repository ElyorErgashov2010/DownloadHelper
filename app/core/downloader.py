"""N_m3u8DL-RE ni ishga tushirish uchun QProcess o'rami."""

import os
import re
import shutil
import sys
from dataclasses import dataclass

from PySide6.QtCore import QObject, QProcess, Signal

# ANSI escape-ketma-ketliklarni olib tashlash uchun regex
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# N_m3u8DL-RE jarayon qatori namunasi: "N/M XX.XX%" mavjud
_PROGRESS_RE = re.compile(r"\d+/\d+\s+\d+(?:\.\d+)?%")

# Ishlash uchun zarur utilitalar
REQUIRED_TOOLS = ["N_m3u8DL-RE", "ffmpeg", "mp4decrypt"]


@dataclass
class ToolStatus:
    """Bitta utilitani qidirish natijasi."""
    name: str
    found: bool
    path: str = ""


def _app_dir() -> str:
    """Exe yonidagi papka (yoki skript yonidagi)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def find_tool(name: str) -> ToolStatus:
    """Utilitani avval PATH dan, keyin dastur yonidan qidiradi."""
    found = shutil.which(name)
    if found:
        return ToolStatus(name=name, found=True, path=found)

    app = _app_dir()
    for suffix in ("", ".exe"):
        candidate = os.path.join(app, name + suffix)
        if os.path.isfile(candidate):
            return ToolStatus(name=name, found=True, path=candidate)

    return ToolStatus(name=name, found=False)


def check_all_tools() -> list[ToolStatus]:
    """Barcha zarur utilitalarning mavjudligini tekshiradi."""
    return [find_tool(name) for name in REQUIRED_TOOLS]


def find_executable() -> str | None:
    """N_m3u8DL-RE ni topish (orqaga moslik uchun)."""
    status = find_tool("N_m3u8DL-RE")
    return status.path if status.found else None


def format_tool_check_log(statuses: list[ToolStatus]) -> str:
    """Utilitalarni tekshirish natijasini log uchun formatlaydi."""
    lines = ["Vositalarni tekshirish:"]
    all_ok = True
    for s in statuses:
        if s.found:
            lines.append(f"  [OK] {s.name} -> {s.path}")
        else:
            lines.append(f"  [TOPILMADI] {s.name}")
            all_ok = False

    if not all_ok:
        lines.append("")
        lines.append(
            "Topilmagan utilitalarni dastur joylashgan papkaga qo'yish "
            "yoki tizim PATH ga qo'shish kerak."
        )
    lines.append("")
    return "\n".join(lines)


class Downloader(QObject):
    # Oddiy log qatori (qator ko'chishlari, xabarlar) — log paneliga boradi
    log_received = Signal(str)
    # Jarayon qatori (\r) — progress-bar va oxirgi qatorni almashtirishga boradi
    progress_received = Signal(str)
    finished = Signal(int)  # chiqish kodi

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)
        self._buffer = ""

    def start(self, args: list[str]):
        """N_m3u8DL-RE ni ishga tushirish. args[0] — bajariladigan fayl yo'li."""
        self._buffer = ""
        exe = args[0]
        self._process.start(exe, args[1:])

    def stop(self):
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(3000)

    def is_running(self) -> bool:
        return self._process.state() != QProcess.ProcessState.NotRunning

    def _on_output(self):
        data = self._process.readAllStandardOutput().data()
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = str(data)

        # ANSI escape-kodlarni olib tashlaymiz
        text = _ANSI_RE.sub("", text)

        self._buffer += text

        while self._buffer:
            # \n yoki \r qidiramiz
            nl = self._buffer.find("\n")
            cr = self._buffer.find("\r")

            if nl == -1 and cr == -1:
                break

            # Eng yaqin ajratuvchini olamiz
            if nl == -1:
                pos, sep = cr, "\r"
            elif cr == -1:
                pos, sep = nl, "\n"
            else:
                pos, sep = (cr, "\r") if cr < nl else (nl, "\n")

            line = self._buffer[:pos]
            self._buffer = self._buffer[pos + 1:]

            if not line.strip():
                continue

            # Jarayon qatorini mazmuni BO'YICHA yoki \r-ajratuvchi orqali aniqlaymiz
            is_progress = sep == "\r" or bool(_PROGRESS_RE.search(line))

            if is_progress:
                self.progress_received.emit(line)
            else:
                self.log_received.emit(line + "\n")

    def _on_finished(self, exit_code, _exit_status):
        # Bufer qoldiqlarini chiqarish
        if self._buffer.strip():
            self.log_received.emit(self._buffer.strip() + "\n")
        self._buffer = ""
        self.finished.emit(exit_code)
