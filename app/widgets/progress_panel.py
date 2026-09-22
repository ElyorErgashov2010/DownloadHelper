"""Yuklab olish jarayoni paneli: progress-bar, tezlik va qolgan vaqt."""

import re

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel


# N_m3u8DL-RE oqim prefikslari (video > audio > subtitr bo'yicha muhim)
_STREAM_PRIORITY = {"vid": 3, "aud": 2, "sub": 1}


class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bar_row = QHBoxLayout()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        bar_row.addWidget(self._progress_bar, 1)
        self._status_label = QLabel("")
        bar_row.addWidget(self._status_label)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addLayout(bar_row)
        layout.addWidget(self._info_label)

        # Har bir oqimning jarayoni: {"vid": 45, "aud": 80, "sub": 0}
        self._stream_progress: dict[str, int] = {}

        # N_m3u8DL-RE uchun regexlar
        self._stream_re = re.compile(r"^(Vid|Aud|Sub)\b", re.IGNORECASE)
        self._pct_re = re.compile(r"(\d+(?:\.\d+)?)%")
        self._fraction_re = re.compile(r"(\d+)/(\d+)")
        self._speed_re = re.compile(
            r"(\d+(?:\.\d+)?\s*(?:Ki?B|Mi?B|Gi?B|[KMG]?B|B)(?:ps|/s))", re.IGNORECASE
        )
        self._time_re = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")

    def reset(self):
        self._progress_bar.setValue(0)
        self._status_label.setText("")
        self._info_label.setText("")
        self._stream_progress.clear()

    def set_progress(self, value: int):
        self._progress_bar.setValue(min(value, 100))

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_info(self, text: str):
        self._info_label.setText(text)

    def parse_output(self, text: str):
        """N_m3u8DL-RE jarayon qatorini tahlil qilib, barni yangilaydi."""
        # Foizni qatordan aniqlash
        pct = -1
        pct_match = self._pct_re.search(text)
        if pct_match:
            pct = int(float(pct_match.group(1)))
        elif (frac := self._fraction_re.search(text)):
            done, total = int(frac.group(1)), int(frac.group(2))
            if total > 0:
                pct = int(done * 100 / total)

        if pct >= 0:
            # Oqimni aniqlash (Vid/Aud/Sub) yoki "unknown"
            stream_match = self._stream_re.match(text.strip())
            stream = stream_match.group(1).lower() if stream_match else "unknown"
            self._stream_progress[stream] = pct

            # Progress-bar eng yuqori prioritetli oqimni ko'rsatadi
            best_pct = self._get_primary_progress()
            self._progress_bar.setValue(best_pct)

        # Ma'lumot (tezlik, vaqt)
        info_parts = []
        speed_match = self._speed_re.search(text)
        if speed_match:
            info_parts.append(f"Tezlik: {speed_match.group(1)}")

        time_matches = self._time_re.findall(text)
        if time_matches:
            info_parts.append(f"Qoldi: {time_matches[-1]}")

        if info_parts:
            self._info_label.setText("  |  ".join(info_parts))

    def _get_primary_progress(self) -> int:
        """Faol oqimning (hali 100% bo'lmagan) jarayonini qaytaradi.

        Agar hali yuklanayotgan (<100%) oqimlar bo'lsa, ulardan eng
        yuqori prioritetlisini ko'rsatadi. Barchasi 100% ga yetgan
        bo'lsa — 100 ni qaytaradi.
        """
        if not self._stream_progress:
            return 0
        # Hali yuklanayotgan oqimlar
        active = {s: p for s, p in self._stream_progress.items() if p < 100}
        if not active:
            return 100
        best_stream = max(
            active,
            key=lambda s: _STREAM_PRIORITY.get(s, 0),
        )
        return active[best_stream]

    def set_finished(self, success: bool):
        if success:
            self._progress_bar.setValue(100)
            self._status_label.setText("Tayyor")
            self._info_label.setText("")
        else:
            self._status_label.setText("Xato")
