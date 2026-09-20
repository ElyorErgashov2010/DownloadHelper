"""Yangi vazifa varag'i uchun ingichka, hover'da kengayadigan scroll bar."""

from PySide6.QtCore import Property, QPropertyAnimation, QEasingCurve, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QAbstractSlider, QScrollBar


class SlimVerticalScrollBar(QScrollBar):
    """Yuqori/pastki uchburchakli va hover'da kengayadigan vertikal scroll bar."""

    _ARROW_HEIGHT = 18
    _NORMAL_HANDLE_WIDTH = 5.0
    _HOVER_HANDLE_WIDTH = 12.0
    _MIN_HANDLE_HEIGHT = 28

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Vertical, parent)
        self.setFixedWidth(18)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._handle_width = self._NORMAL_HANDLE_WIDTH
        self._dragging = False
        self._drag_offset = 0
        self._hover_animation = QPropertyAnimation(self, b"handleWidth", self)
        self._hover_animation.setDuration(140)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_handle_width(self) -> float:
        return self._handle_width

    def _set_handle_width(self, value: float):
        self._handle_width = value
        self.update()

    handleWidth = Property(float, _get_handle_width, _set_handle_width)

    def sizeHint(self) -> QSize:
        """QScrollArea 18 px kenglik ajratishi uchun haqiqiy size hint."""
        hint = super().sizeHint()
        return QSize(18, hint.height())

    def _animate_handle(self, target: float):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._handle_width)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def _groove_rect(self) -> QRect:
        top = self._ARROW_HEIGHT
        height = max(1, self.height() - self._ARROW_HEIGHT * 2)
        return QRect(0, top, self.width(), height)

    def _handle_rect(self) -> QRect:
        groove = self._groove_rect()
        value_range = self.maximum() - self.minimum()
        if value_range <= 0:
            handle_height = groove.height()
            ratio = 0.0
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

        width = max(3, round(self._handle_width))
        return QRect((self.width() - width) // 2, groove.top(), width, handle_height)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        groove = self._groove_rect()
        handle = self._handle_rect()

        # Ingichka yo'l (track).
        track_color = QColor("#4f4f4f") if self.underMouse() else QColor("#3d3d3d")
        painter.setPen(QPen(track_color, 2))
        painter.drawLine(center_x, groove.top(), center_x, groove.bottom())

        # Har doim ko'rinib turadigan yuqori va pastki uchburchaklar.
        arrow_color = QColor("#c0c0c0") if self.underMouse() else QColor("#8f8f8f")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(arrow_color)
        painter.drawPolygon(QPolygon([
            self._point(center_x, 4),
            self._point(center_x - 5, 12),
            self._point(center_x + 5, 12),
        ]))
        bottom = self.height()
        painter.drawPolygon(QPolygon([
            self._point(center_x, bottom - 4),
            self._point(center_x - 5, bottom - 12),
            self._point(center_x + 5, bottom - 12),
        ]))

        # Qimirlaydigan tutqich (handle).
        if self._dragging:
            handle_color = QColor("#55b7ef")
        elif self.underMouse():
            handle_color = QColor("#a9a9a9")
        else:
            handle_color = QColor("#777777")
        painter.setBrush(handle_color)
        painter.drawRoundedRect(handle, handle.width() / 2, handle.width() / 2)

    @staticmethod
    def _point(x: int, y: int):
        from PySide6.QtCore import QPoint
        return QPoint(x, y)

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
            self.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepSub)
            self.setRepeatAction(
                QAbstractSlider.SliderAction.SliderSingleStepSub,
                400,
                50,
            )
        elif pos.y() >= self.height() - self._ARROW_HEIGHT:
            self.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepAdd)
            self.setRepeatAction(
                QAbstractSlider.SliderAction.SliderSingleStepAdd,
                400,
                50,
            )
        elif handle.contains(pos):
            self._dragging = True
            self._drag_offset = pos.y() - handle.top()
        elif pos.y() < handle.top():
            self.setValue(max(self.minimum(), self.value() - self.pageStep()))
        else:
            self.setValue(min(self.maximum(), self.value() + self.pageStep()))
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
            self.setRepeatAction(QAbstractSlider.SliderAction.SliderNoAction)
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._animate_handle(
                self._HOVER_HANDLE_WIDTH if self.underMouse() else self._NORMAL_HANDLE_WIDTH
            )
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
