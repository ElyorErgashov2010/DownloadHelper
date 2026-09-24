"""Windows Explorer'ga o'xshash ingichka vertikal scroll bar.

Xulq:

- Oddiy holatda (sichqoncha bormagan): faqat ingichka tutqich (tayoqcha).
- Sichqoncha borganda: tutqich kengayadi, fon yo'li ochiladi va ▲/▼
  uchburchak tugmalar chiqadi.
- ▲/▼ ni yoki yo'lni bosib turilganda scroll auto-repeat bilan to'xtovsiz
  davom etadi, qo'yib yuborilganda to'xtaydi.
"""

from PySide6.QtCore import (
    Property, QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer,
)
from PySide6.QtGui import QColor, QPainter, QPolygon
from PySide6.QtWidgets import QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Ingichka, hover'da kengayadigan Explorer-uslub vertikal scroll bar."""

    _ARROW_HEIGHT = 14          # ▲/▼ uchburchak bosish zonalari balandligi
    _ARROW_HALF_WIDTH = 5       # uchburchak kengligining yarmi
    _NORMAL_HANDLE_WIDTH = 5.0  # oddiy holatdagi tutqich kengligi
    _HOVER_HANDLE_WIDTH = 11.0  # hover holatidagi tutqich kengligi
    _MIN_HANDLE_HEIGHT = 24
    _REPEAT_DELAY_MS = 400      # bosish → takrorlash boshlanguncha kutish
    _REPEAT_INTERVAL_MS = 50    # takrorlash oralig'i

    def __init__(self, parent=None, *, framed_on_hover: bool = False, extent: int = 18):
        super().__init__(Qt.Orientation.Vertical, parent)
        self._extent = extent
        self._framed_on_hover = framed_on_hover
        self.setFixedWidth(extent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._handle_width = self._NORMAL_HANDLE_WIDTH
        self._dragging = False
        self._drag_offset = 0
        self._repeat_delta = 0

        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._repeat_scroll_step)

        self._hover_animation = QPropertyAnimation(self, b"handleWidth", self)
        self._hover_animation.setDuration(120)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Attraktsion xususiyat (tutqich kengligi animatsiyasi) ──────

    def _get_handle_width(self) -> float:
        return self._handle_width

    def _set_handle_width(self, value: float):
        self._handle_width = value
        self.update()

    handleWidth = Property(float, _get_handle_width, _set_handle_width)

    # ── O'lcham ──────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(self._extent, hint.height())

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(self._extent, hint.height())

    # ── Geometriya ───────────────────────────────────────────────

    def _groove_top(self) -> int:
        return self._ARROW_HEIGHT

    def _groove_height(self) -> int:
        return max(1, self.height() - 2 * self._ARROW_HEIGHT)

    def _handle_rect(self) -> QRect:
        groove_top = self._groove_top()
        groove_height = self._groove_height()
        value_range = self.maximum() - self.minimum()
        if value_range <= 0:
            handle_height = groove_height
            y = groove_top
        else:
            page = max(1, self.pageStep())
            handle_height = max(
                self._MIN_HANDLE_HEIGHT,
                round(groove_height * page / (value_range + page)),
            )
            handle_height = min(groove_height, handle_height)
            usable = max(1, groove_height - handle_height)
            ratio = (self.value() - self.minimum()) / value_range
            ratio = max(0.0, min(1.0, ratio))
            y = groove_top + round(usable * ratio)

        width = max(3, round(self._handle_width))
        return QRect((self.width() - width) // 2, y, width, handle_height)

    def _arrow_polygon(self, upward: bool) -> QPolygon:
        center_x = self.width() // 2
        half = self._ARROW_HALF_WIDTH
        if upward:
            return QPolygon([
                QPoint(center_x, 3),
                QPoint(center_x - half, 12),
                QPoint(center_x + half, 12),
            ])
        bottom = self.height()
        return QPolygon([
            QPoint(center_x, bottom - 3),
            QPoint(center_x - half, bottom - 12),
            QPoint(center_x + half, bottom - 12),
        ])

    # ── Chizish ──────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        hovered = self.underMouse() or self._dragging
        handle = self._handle_rect()
        width = self.width()

        # Fon yo'li.
        if hovered:
            track_width = max(10, round(self._handle_width) + 3)
            track = QRect((width - track_width) // 2, 0, track_width, self.height())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#343434"))
            painter.drawRoundedRect(track, track_width / 2.0, track_width / 2.0)
        elif self._framed_on_hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#3a3a3a"))
            painter.drawRect(QRect(0, 0, width, self.height()))

        # ▲/▼ uchburchaklar — faqat hover'da (Windows Explorer uslubi).
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#c9c9c9"))
            painter.drawPolygon(self._arrow_polygon(True))
            painter.drawPolygon(self._arrow_polygon(False))

        # Tutqich.
        if self._dragging:
            handle_color = QColor("#59b9ed")
        elif hovered:
            handle_color = QColor("#aeaeae")
        else:
            handle_color = QColor("#7b7b7b")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        painter.drawRoundedRect(handle, handle.width() / 2.0, handle.width() / 2.0)

    # ── Takrorlanadigan scroll (auto-repeat) ─────────────────────

    def _start_repeat(self, delta: int):
        self._repeat_delta = delta
        self._apply_delta(delta)
        self._repeat_timer.start(self._REPEAT_DELAY_MS)

    def _repeat_scroll_step(self):
        if not self._repeat_delta:
            return
        self._apply_delta(self._repeat_delta)
        self._repeat_timer.start(self._REPEAT_INTERVAL_MS)

    def _apply_delta(self, delta: int):
        self.setValue(max(self.minimum(), min(self.maximum(), self.value() + delta)))

    def _stop_repeat(self):
        self._repeat_delta = 0
        self._repeat_timer.stop()

    # ── Sichqoncha hodisalari ────────────────────────────────────

    def enterEvent(self, event):
        self._animate_handle(self._HOVER_HANDLE_WIDTH)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._dragging:
            self._animate_handle(self._NORMAL_HANDLE_WIDTH)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()
        handle = self._handle_rect()
        if pos.y() < self._ARROW_HEIGHT:
            self._start_repeat(-self.singleStep())
        elif pos.y() >= self.height() - self._ARROW_HEIGHT:
            self._start_repeat(self.singleStep())
        elif handle.contains(pos):
            self._dragging = True
            self._drag_offset = pos.y() - handle.top()
        elif pos.y() < handle.top():
            self._start_repeat(-self.pageStep())
        else:
            self._start_repeat(self.pageStep())
        self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging:
            super().mouseMoveEvent(event)
            return

        groove_top = self._groove_top()
        groove_height = self._groove_height()
        handle = self._handle_rect()
        usable = max(1, groove_height - handle.height())
        new_top = round(event.position().toPoint().y()) - self._drag_offset
        new_top = max(groove_top, min(groove_top + usable, new_top))
        ratio = (new_top - groove_top) / usable
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._stop_repeat()
            if self._dragging:
                self._dragging = False
                self._animate_handle(
                    self._HOVER_HANDLE_WIDTH if self.underMouse() else self._NORMAL_HANDLE_WIDTH
                )
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _animate_handle(self, target: float):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._handle_width)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()
