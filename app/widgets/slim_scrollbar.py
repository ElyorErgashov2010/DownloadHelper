"""Windows Explorer'ga o'xshash ingichka vertikal scroll bar.

Xulq:
- Oddiy holatda (sichqoncha bormagan): faqat ingichka tutqich (tayoqcha).
- Sichqoncha borganda: tutqich kengayadi, fon yo'li ochiladi va ▲/▼
  uchburchak tugmalar chiqadi.
- ▲/▼ ni yoki yo'lni bosib turilganda scroll auto-repeat bilan to'xtovsiz
  davom etadi, qo'yib yuborilganda to'xtaydi.

Geometriya:
- Track, tutqich va uchburchaklar widget kengligi bo'yicha MARKAZDA
  chiziladi — chap qirrada kesilish, o'ngda ortiqcha bo'sh joy qolmaydi.
- Ramkali (framed) scroll barlar kengroq joy oladi (extent, 18px);
  oramasiz asosiy scroll bar 12px da qoladi.
"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Ingichka, hover'da kengayadigan, markazdan chiziladigan vertikal scroll bar."""

    _MIN_HANDLE_HEIGHT = 20.0
    _REPEAT_DELAY_MS = 400      # bosish → takrorlash boshlanguncha kutish
    _REPEAT_INTERVAL_MS = 50    # takrorlash oralig'i

    _ARROW_HALF_WIDTH = 4.5     # uchburchak kengligining yarmi
    _ARROW_HEIGHT = 5.5         # uchburchak balandligi

    def __init__(self, parent=None, *, framed_on_hover: bool = False, extent: int = 18):
        super().__init__(Qt.Orientation.Vertical, parent)
        self._extent = extent
        self._framed_on_hover = framed_on_hover

        # Grafik asoratlarni oldini olish uchun fonni shaffof qilamiz
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Zargarlik aniqligida sozlangan daxlsiz o'lchamlar (7px normal / 12px hover)
        self.normal_width = 7
        self.hover_width = 12

        # Ramkali scroll barlar (Buyruq, Navbat, Log) uchun joy kengroq —
        # extent (18px). Oramasiz asosiy scroll bar esa 12px da qoladi.
        self._widget_width = extent if framed_on_hover else self.hover_width
        self.setFixedWidth(self._widget_width)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._dragging = False
        self._drag_offset = 0
        self._repeat_delta = 0
        self.is_hovered = False

        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._repeat_scroll_step)

    # ── O'lchamlar ───────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(self._widget_width, super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self._widget_width, super().minimumSizeHint().height())

    # ── Ichki Geometriya Hisob-kitoblari (barchasi markazda) ─────

    def _groove_top(self) -> float:
        return 17.0                     # Tepa uchburchak va tayoqcha orasidagi masofa

    def _groove_bottom(self) -> float:
        return 17.0                     # Pastki uchburchak va tayoqcha orasidagi masofa

    def _track_width(self) -> float:
        # Chizish kengligi qirralardan 2px masofada turadi: uchburchaklar
        # (±4.5px) hech qachon chetga kesilmaydi.
        margin = 2.0
        if self.is_hovered or self._dragging:
            return self.hover_width - margin    # 10px
        return self.normal_width - margin       # 5px

    def _track_rect(self) -> QRectF:
        track_width = self._track_width()
        x_pos = (self.width() - track_width) / 2.0
        return QRectF(
            x_pos,
            self._groove_top(),
            track_width,
            self.height() - (self._groove_top() + self._groove_bottom()),
        )

    def _handle_rect(self) -> QRectF:
        track = self._track_rect()
        value_range = self.maximum() - self.minimum()
        available_height = track.height()

        if value_range <= 0:
            return QRectF(track.left(), track.top(), track.width(), available_height)

        page = max(1, self.pageStep())
        handle_height = max(
            self._MIN_HANDLE_HEIGHT,
            available_height * page / (value_range + page)
        )
        if handle_height > available_height:
            handle_height = available_height

        usable = available_height - handle_height
        ratio = (self.value() - self.minimum()) / value_range
        ratio = max(0.0, min(1.0, ratio))
        y = track.top() + (usable * ratio)

        return QRectF(track.left(), y, track.width(), handle_height)

    # ── Grafik Chizish (Paint Event) ─────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        hovered = self.underMouse() or self._dragging
        track = self._track_rect()
        handle = self._handle_rect()
        center_x = track.left() + track.width() / 2.0

        # 1. Orqa fon: ramkali scroll barlarda doimiy kulrang tasma
        if self._framed_on_hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#3a3a3a"))
            painter.drawRect(QRectF(0, 0, self.width(), self.height()))

        # 2. Hover'da tasma ustiga to'rtburchakli fon yo'li (Track)
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#252526"))
            track_radius = track.width() / 2.0
            painter.drawRoundedRect(track, track_radius, track_radius)

        # 2. ▲ TEPA va ▼ PASTKI UCHBURCHAKLAR — faqat hover'da,
        #    track o'qi bo'yicha markazda (chetlarda kesilmaydi)
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#aaaaaa"))
            half = self._ARROW_HALF_WIDTH
            h = self._ARROW_HEIGHT
            up_arrow = QPolygonF([
                QPointF(center_x, 3.0),
                QPointF(center_x - half, 3.0 + h),
                QPointF(center_x + half, 3.0 + h),
            ])
            painter.drawPolygon(up_arrow)
            bottom_y = self.height() - 3.0
            down_arrow = QPolygonF([
                QPointF(center_x, bottom_y),
                QPointF(center_x - half, bottom_y - h),
                QPointF(center_x + half, bottom_y - h),
            ])
            painter.drawPolygon(down_arrow)

        # 3. SURILUVCHI TAYOQCHANI (Handle) CHIZISH
        if self._dragging:
            handle_color = QColor("#59b9ed")  # Sudralgandagi ko'k effekt daxlsiz saqlandi
        elif hovered:
            handle_color = QColor("#888888")
        else:
            handle_color = QColor("#555555")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        handle_radius = handle.width() / 2.0
        painter.drawRoundedRect(handle, handle_radius, handle_radius)
        painter.end()

    # ── Auto-repeat (Bosib turgandagi uzluksiz harakat) ──────────

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

    # ── Sichqoncha Hodisalari (Events) ───────────────────────────

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
        arrow_h = int(self._groove_top())

        if pos.y() < arrow_h:
            self._start_repeat(-self.singleStep())
        elif pos.y() >= self.height() - arrow_h:
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
        track = self._track_rect()
        handle = self._handle_rect()
        usable = max(1.0, track.height() - handle.height())

        new_top = event.position().y() - self._drag_offset
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
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
