"""Windows 7 Explorer'a o'xshash, jonli «yashil to'lqin»li progress bar.

Barcha platformalarda bir xil ko'rinish berish uchun Qt native progress bar
o'rniga `paintEvent` da qo'lda chiziladi:

- Pastki yo'l (groove): och kulrang, yumaloq burchakli.
- Yashil to'ldirish: foizga qarab o'ngga o'sib boradi.
- To'lqin: yashil hududning markazida o'ngga jonli o'tadigan sinusoidal
  yashil-oq to'lqin (Windows 7 uslubi).
- Foiz: bar markazida, to'lqin ustida oq rangda.
"""

import math

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QProgressBar, QSizePolicy


class WaveProgressBar(QProgressBar):
    """Jonli yashil to'lqinli progress bar."""

    _WAVE_AMPLITUDE = 5.0   # to'lqin balandligi
    _WAVE_LENGTH = 34.0     # bitta to'lqin davrining uzunligi (px)

    def __init__(self, parent=None, *, show_percent: bool = True):
        super().__init__(parent)
        self._show_percent = show_percent
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(38)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self._wave_shift = 0.0
        self._tick = 0.0

        self._drift_timer = QTimer(self)
        self._drift_timer.setInterval(30)
        self._drift_timer.timeout.connect(self._on_drift_tick)
        self._drift_timer.start()

    # ── Jonli harakat ────────────────────────────────────────────

    def _on_drift_tick(self):
        self._tick += 0.03
        # Windows 7 dagiga o'xshash nozik pulsatsiya: tezlik sal o'zgarib turadi.
        speed = 1.7 + 0.7 * math.sin(self._tick * 1.6)
        self._wave_shift = (self._wave_shift + speed) % self._WAVE_LENGTH
        self.update()

    # ── Chizish ──────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar = self.rect().adjusted(1, 1, -1, -1)
        radius = bar.height() / 2.0

        self._draw_groove(painter, bar, radius)

        value = max(0, min(100, self.value()))
        fill_width = bar.width() * value / 100.0
        if fill_width >= 1.0:
            fill_rect = QRectF(bar.left(), bar.top(), fill_width, bar.height())
            clip = QPainterPath()
            clip.addRoundedRect(QRectF(bar), radius, radius)
            painter.save()
            painter.setClipPath(clip)
            self._draw_fill(painter, fill_rect)
            self._draw_wave(painter, fill_rect)
            painter.restore()

        if self._show_percent:
            self._draw_percent(painter, bar)

        painter.end()

    def _draw_groove(self, painter, bar, radius):
        """Pastki yo'l (groove)."""
        grad = QLinearGradient(0, bar.top(), 0, bar.bottom())
        grad.setColorAt(0.0, QColor("#c8c8c8"))
        grad.setColorAt(0.5, QColor("#f1f1f1"))
        grad.setColorAt(1.0, QColor("#d2d2d2"))
        painter.setPen(QPen(QColor("#8c8c8c"), 1))
        painter.setBrush(grad)
        painter.drawRoundedRect(QRectF(bar), radius, radius)

    def _draw_fill(self, painter, fill_rect):
        """Yashil to'ldirish hududi."""
        grad = QLinearGradient(0, fill_rect.top(), 0, fill_rect.bottom())
        grad.setColorAt(0.0, QColor("#7adf52"))
        grad.setColorAt(0.5, QColor("#5ec93f"))
        grad.setColorAt(1.0, QColor("#40a826"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRect(fill_rect)

    def _draw_wave(self, painter, fill_rect):
        """Yashil hudud markazida o'ngga o'tadigan to'lqin chizadi."""
        center_y = fill_rect.center().y()
        amp = min(self._WAVE_AMPLITUDE, fill_rect.height() * 0.3)
        length = self._WAVE_LENGTH
        shift = self._wave_shift
        left = fill_rect.left()
        right = fill_rect.right()

        painter.save()
        painter.setClipRect(fill_rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Asosiy, och yashil to'lqin chizig'i.
        painter.setPen(QPen(
            QColor("#c4f1ad"), 3.2, Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
        ))
        path = QPainterPath()
        first = True
        x = left
        while x <= right:
            y = center_y - amp * math.sin(2 * math.pi * (x + shift) / length)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
            x += 1.6
        painter.drawPath(path)

        # To'lqin tepalarida ingichka oq porlash.
        painter.setPen(QPen(QColor(255, 255, 255, 170), 1.4))
        path2 = QPainterPath()
        first = True
        x = left
        while x <= right:
            y = center_y - amp * math.sin(2 * math.pi * (x + shift) / length) - 1.8
            if first:
                path2.moveTo(x, y)
                first = False
            else:
                path2.lineTo(x, y)
            x += 1.6
        painter.drawPath(path2)

        painter.restore()

    def _draw_percent(self, painter, bar):
        """Foiz yozuvini bar markazida, to'lqin ustida chizadi.

        Yozuv to'lqin ustidan chiqib ko'rinishi uchun oq matn atrofida
        nozik qoramtir kontur ishlatiladi (och yorug' yo'lda ham o'qiladi).
        """
        text = f"{self.value()}%"
        font = QFont(self.font())
        font.setBold(True)
        font.setPixelSize(max(13, int(bar.height() * 0.42)))
        painter.setFont(font)
        metrics = painter.fontMetrics()

        x = (bar.width() - metrics.horizontalAdvance(text)) / 2.0
        baseline = bar.center().y() + (metrics.ascent() - metrics.descent()) / 2.0

        path = QPainterPath()
        path.addText(x, baseline, font, text)

        # Qoramtir kontur — yozuvni to'lqin va yo'ldan ajratib turadi.
        painter.setPen(QPen(QColor(0, 0, 0, 170), 2.2,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
        # Oq ichki matn.
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
