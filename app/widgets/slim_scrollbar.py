"""Windows Explorer'ga o'xshash ingichka vertikal scroll bar."""

from PySide6.QtCore import Property, QPropertyAnimation, QEasingCurve, QRect, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Oddiy holatda ramkasiz, hover'da kattalashadigan Explorer-uslub scroll."""

    _NORMAL_HANDLE_WIDTH = 5.0
    _HOVER_HANDLE_WIDTH = 9.0
    _MIN_HANDLE_HEIGHT = 28

    def __init__(self, parent=None, *, framed_on_hover: bool = False, extent: int = 14):
        super().__init__(Qt.Orientation.Vertical, parent)
        self._extent = extent
        # Eski chaqiruvlar bilan moslik uchun saqlanadi. Hover dizayni barcha
        # scroll'larda Explorer uslubida bir xil ishlaydi.
        self._framed_on_hover = framed_on_hover
        self.setFixedWidth(extent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._handle_width = self._NORMAL_HANDLE_WIDTH
        self._dragging = False
        self._drag_offset = 0
        self._repeat_delta = 0
        self._repeat_timer = QTimer(self)
        self._repeat_timer.setSingleShot(True)
        self._repeat_timer.timeout.connect(self._repeat_scroll_step)
        self._hover_animation = QPropertyAnimation(self, b"handleWidth", self)
        self._hover_animation.setDuration(120)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_handle_width(self) -> float:
        return self._handle_width

    def _set_handle_width(self, value: float):
        self._handle_width = value
        self.update()

    handleWidth = Property(float, _get_handle_width, _set_handle_width)

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(self._extent, hint.height())

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(self._extent, hint.height())

    def _start_repeat_scroll(self, delta: int):
        """Track ustida bosib turilganda Explorer kabi page scroll'ni takrorlaydi."""
        self._repeat_delta = delta
        self.setValue(max(self.minimum(), min(self.maximum(), self.value() + delta)))
        self._repeat_timer.start(400)

    def _repeat_scroll_step(self):
        if not self._repeat_delta:
            return
        self.setValue(
            max(self.minimum(), min(self.maximum(), self.value() + self._repeat_delta))
        )
        self._repeat_timer.start(80)

    def _stop_repeat_scroll(self):
        self._repeat_delta = 0
        self._repeat_timer.stop()

    def _animate_handle(self, target: float):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._handle_width)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def _groove_rect(self) -> QRect:
        # Explorer kabi alohida ▲/▼ tugmalari va tashqi ramka yo'q.
        return QRect(0, 0, self.width(), max(1, self.height()))

    def _handle_rect(self) -> QRect:
        groove = self._groove_rect()
        value_range = self.maximum() - self.minimum()
        if value_range <= 0:
            handle_height = groove.height()
            y = groove.top()
        else:
            page = max(1, self.pageStep())
            handle_height = max(
                self._MIN_HANDLE_HEIGHT,
                round(groove.height() * page / (value_range + page)),
            )
            handle_height = min(groove.height(), handle_height)
            usable_height = max(1, groove.height() - handle_height)
            ratio = (self.value() - self.minimum()) / value_range
            ratio = max(0.0, min(1.0, ratio))
            y = groove.top() + round(usable_height * ratio)

        width = max(3, round(self._handle_width))
        return QRect((self.width() - width) // 2, y, width, handle_height)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        hovered = self.underMouse() or self._dragging
        handle = self._handle_rect()

        # Sichqoncha yo'q bo'lsa: faqat ingichka tutqich. Hover'da: Explorer
        # uslubidagi kengroq, lekin ramkasiz fon yo'li.
        if hovered:
            track_width = max(10, round(self._handle_width) + 3)
            track = QRect(
                (self.width() - track_width) // 2,
                0,
                track_width,
                self.height(),
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#343434"))
            painter.drawRoundedRect(track, track_width / 2, track_width / 2)

        if self._dragging:
            handle_color = QColor("#59b9ed")
        elif hovered:
            handle_color = QColor("#a6a6a6")
        else:
            handle_color = QColor("#7b7b7b")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        painter.drawRoundedRect(handle, handle.width() / 2, handle.width() / 2)

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
        if handle.contains(pos):
            self._dragging = True
            self._drag_offset = pos.y() - handle.top()
        elif pos.y() < handle.top():
            self._start_repeat_scroll(-self.pageStep())
        else:
            self._start_repeat_scroll(self.pageStep())
        self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging:
            super().mouseMoveEvent(event)
            return

        groove = self._groove_rect()
        handle = self._handle_rect()
        usable_height = max(1, groove.height() - handle.height())
        new_top = event.position().toPoint().y() - self._drag_offset
        new_top = max(groove.top(), min(groove.top() + usable_height, new_top))
        ratio = (new_top - groove.top()) / usable_height
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._stop_repeat_scroll()
            if self._dragging:
                self._dragging = False
                self._animate_handle(
                    self._HOVER_HANDLE_WIDTH if self.underMouse() else self._NORMAL_HANDLE_WIDTH
                )
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
