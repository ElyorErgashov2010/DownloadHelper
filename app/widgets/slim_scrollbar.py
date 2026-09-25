"""Windows Explorer'ga o'xshash ingichka vertikal scroll bar.

Xulq:
- Oddiy holatda (sichqoncha bormagan): faqat ingichka tutqich (tayoqcha).
- Sichqoncha borganda: tutqich kengayadi, fon yo'li ochiladi va ▲/▼ uchburchak tugmalar chiqadi.
- ▲/▼ ni yoki yo'lni bosib turilganda scroll auto-repeat bilan to'xtovsiz davom etadi.
"""

from PySide6.QtCore import (
    Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, QEvent
)
from PySide6.QtGui import QColor, QPainter, QPolygonF, QPen
from PySide6.QtWidgets import QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Ingichka, hover'da kengayadigan mutloq silliq va qirrasiz vertikal scroll bar."""

    _MIN_HANDLE_HEIGHT = 20.0
    _REPEAT_DELAY_MS = 400      # bosish → takrorlash boshlanguncha kutish
    _REPEAT_INTERVAL_MS = 50    # takrorlash oralig'i

    def __init__(self, parent=None, *, framed_on_hover: bool = False, extent: int = 18):
        super().__init__(Qt.Orientation.Vertical, parent)
        self._extent = extent
        self._framed_on_hover = framed_on_hover
        
        # Grafik asoratlarni oldini olish uchun fonni shaffof qilamiz
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Siz zargarlik aniqligida sozlagan daxlsiz o'lchamlar (7px normal / 12px hover)
        self.normal_width = 7         
        self.hover_width = 12          
        self.setFixedWidth(self.hover_width)
        
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._dragging = False
        self._drag_offset = 0
        self._repeat_delta = 0
        self.is_hovered = False

        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._repeat_scroll_step)

    # ── O'lchamlar (Loyihaga moslik) ──────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(self.hover_width, super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self.hover_width, super().minimumSizeHint().height())

    # ── Ichki Geometriya Hisob-kitoblari ──────────────────────────

    def _groove_top(self) -> float:
        return 17.0                     # Tepa uchburchak va tayoqcha orasidagi masofa

    def _groove_bottom(self) -> float:
        return 17.0                     # Pastki uchburchak va tayoqcha orasidagi masofa

    def _track_rect(self) -> QRectF:
        right_m = 5
        top_m = self._groove_top()
        bottom_m = self._groove_bottom()

        if self.is_hovered or self._dragging:
            x_pos = 0.0
            current_width = self.hover_width - right_m
        else:
            x_pos = 5.0
            current_width = self.normal_width - right_m

        return QRectF(
            x_pos, 
            top_m, 
            current_width, 
            self.height() - (top_m + bottom_m)
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

        # 1. Orqa fon yo'lini (Track) chizish
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#252526"))
            track_radius = track.width() / 2.0
            painter.drawRoundedRect(track, track_radius, track_radius)
        elif self._framed_on_hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#3a3a3a"))
            painter.drawRect(QRectF(0, 0, self.width(), self.height()))

        # Uchburchak qirralarini mutloq silliq qiluvchi maxsus qalam
        arrow_color = QColor("#aaaaaa") if hovered else Qt.GlobalColor.transparent
        arrow_pen = QPen(arrow_color)
        arrow_pen.setWidthF(1.5)                         
        arrow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin) 
        arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)   

        # 2. ▲ TEPA UCHBURCHAK O'QINI CHIZISH
        if arrow_color != Qt.GlobalColor.transparent:
            painter.setPen(arrow_pen)
            painter.setBrush(arrow_color) 
            center_x = track.left() + track.width() / 2.0
            up_arrow = QPolygonF([
                QPointF(center_x, 3.0),          
                QPointF(center_x - 4.5, 8.5),   
                QPointF(center_x + 4.5, 8.5)    
            ])
            painter.drawPolygon(up_arrow)

        # 3. ▼ PASTKI UCHBURCHAK O'QINI CHIZISH
        if arrow_color != Qt.GlobalColor.transparent:
            painter.setPen(arrow_pen)
            painter.setBrush(arrow_color) 
            center_x = track.left() + track.width() / 2.0
            bottom_y = self.height() - 3.0       
            down_arrow = QPolygonF([
                QPointF(center_x, bottom_y),          
                QPointF(center_x - 4.5, bottom_y - 5.5), 
                QPointF(center_x + 4.5, bottom_y - 5.5)  
            ])
            painter.drawPolygon(down_arrow)

        # 4. SURILUVCHI TAYOQCHANI (Handle) CHIZISH
        if self._dragging:
            handle_color = QColor("#59b9ed") # Sudralgandagi ko'k effekt daxlsiz saqlandi
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
