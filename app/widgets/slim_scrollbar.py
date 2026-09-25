"""Windows Explorer'ga o'xshash ingichka vertikal scroll bar.

Xulq:

- Oddiy holatda (sichqoncha bormagan): faqat ingichka tutqich (tayoqcha).
- Sichqoncha borganda: tutqich kengayadi, fon yo'li ochiladi va ▲/▼
  uchburchak tugmalar chiqadi.
- ▲/▼ ni yoki yo'lni bosib turilganda scroll auto-repeat bilan to'xtovsiz
  davom etadi, qo'yib yuborilganda to'xtaydi.
- Hammasi (yo'l, tutqich, uchburchaklar) scroll bar yo'lagining markazida,
  o'ngga/chapga surilib kesilmaydi.
"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Ingichka, hover'da kengayadigan Explorer-uslub vertikal scroll bar."""

    _ARROW_ZONE = 16.0           # ▲/▼ bosish zonalari balandligi (tepada va pastda)
    _ARROW_HALF_WIDTH = 4.5      # uchburchak kengligining yarmi
    _NORMAL_HANDLE_WIDTH = 7.0   # oddiy holatdagi tutqich kengligi
    _HOVER_HANDLE_WIDTH = 12.0   # hover holatidagi tutqich kengligi
    _MIN_HANDLE_HEIGHT = 20.0
    _REPEAT_DELAY_MS = 400       # bosish → takrorlash boshlanguncha kutish
    _REPEAT_INTERVAL_MS = 50     # takrorlash oralig'i

    def __init__(self, parent=None, *, framed_on_hover: bool = False, extent: int = 18):
        super().__init__(Qt.Orientation.Vertical, parent)
        self._extent = extent
        self._framed_on_hover = framed_on_hover

        # Grafik asoratlarni oldini olish uchun fonni shaffof qilamiz.
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.normal_width = self._NORMAL_HANDLE_WIDTH
        self.hover_width = self._HOVER_HANDLE_WIDTH
        # Yo'lak kengligi har bir scroll bar uchun alohida belgilanadi
        # (asosiy forma uchun 18, ichki maydonlar uchun ham 18).
        self.setFixedWidth(extent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._dragging = False
        self._drag_offset = 0
        self._repeat_delta = 0
        self.is_hovered = False

        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._repeat_scroll_step)

    # ── O'lcham ──────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(self._extent, super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self._extent, super().minimumSizeHint().height())

    # ── Geometriya ───────────────────────────────────────────────

    def _active_handle_width(self) -> float:
        if self.is_hovered or self._dragging:
            return self.hover_width
        return self.normal_width

    def _track_rect(self) -> QRectF:
        """Yo'l to'rtburchagi — yo'lak o'rtasida markazlanadi."""
        w = self._active_handle_width()
        x = (self.width() - w) / 2.0
        m = self._ARROW_ZONE
        height = max(1.0, self.height() - 2.0 * m)
        return QRectF(x, m, w, height)

    def _handle_rect(self) -> QRectF:
        track = self._track_rect()
        value_range = self.maximum() - self.minimum()
        if value_range <= 0:
            return QRectF(track.left(), track.top(), track.width(), track.height())

        page = max(1, self.pageStep())
        handle_height = max(
            self._MIN_HANDLE_HEIGHT,
            track.height() * page / (value_range + page),
        )
        handle_height = min(handle_height, track.height())

        usable = track.height() - handle_height
        ratio = (self.value() - self.minimum()) / value_range
        ratio = max(0.0, min(1.0, ratio))
        y = track.top() + usable * ratio
        return QRectF(track.left(), y, track.width(), handle_height)

    def _arrow_polygon(self, upward: bool) -> QPolygonF:
        center_x = self.width() / 2.0
        half = self._ARROW_HALF_WIDTH
        if upward:
            return QPolygonF([
                QPointF(center_x, 3.0),
                QPointF(center_x - half, 9.0),
                QPointF(center_x + half, 9.0),
            ])
        bottom = float(self.height())
        return QPolygonF([
            QPointF(center_x, bottom - 3.0),
            QPointF(center_x - half, bottom - 9.0),
            QPointF(center_x + half, bottom - 9.0),
        ])

    # ── Chizish ──────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        hovered = self.is_hovered or self._dragging
        track = self._track_rect()
        handle = self._handle_rect()

        # 1. Orqa fon yo'li (track).
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#252526"))
            radius = track.width() / 2.0
            painter.drawRoundedRect(track, radius, radius)
        elif self._framed_on_hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#3a3a3a"))
            painter.drawRect(QRectF(0, 0, self.width(), self.height()))

        # 2. ▲ / ▼ uchburchaklar — faqat hover'da.
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#aaaaaa"))
            painter.drawPolygon(self._arrow_polygon(True))
            painter.drawPolygon(self._arrow_polygon(False))

        # 3. Suriluvchi tayoqcha (handle).
        if self._dragging:
            handle_color = QColor("#59b9ed")
        elif hovered:
            handle_color = QColor("#888888")
        else:
            handle_color = QColor("#555555")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        radius = handle.width() / 2.0
        painter.drawRoundedRect(handle, radius, radius)
        painter.end()

    # ── Auto-repeat (bosib turgandagi uzluksiz harakat) ──────────

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
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()
        handle = self._handle_rect().toRect()
        arrow_zone = int(self._ARROW_ZONE)

        if pos.y() < arrow_zone:
            self._start_repeat(-self.singleStep())
        elif pos.y() >= self.height() - arrow_zone:
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

        track = self._track_rect()
        handle = self._handle_rect()
        usable = max(1.0, track.height() - handle.height())

        new_top = event.position().y() - self._drag_offset
        new_top = max(track.top(), min(track.top() + usable, new_top))

        ratio = (new_top - track.top()) / usable
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._stop_repeat()
            if self._dragging:
                self._dragging = False
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
