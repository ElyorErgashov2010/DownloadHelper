"""Radio va checkbox uchun barcha tizimlarda bir xil ko'rinadigan indikatorlar."""

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QProxyStyle, QStyle


class SelectionIndicatorStyle(QProxyStyle):
    """Fusion style ustida oldingi dizaynga o'xshash ko'k tanlash belgilarini chizadi."""

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            self._draw_checkbox(option, painter)
            return
        if element == QStyle.PrimitiveElement.PE_IndicatorRadioButton:
            self._draw_radio(option, painter)
            return
        super().drawPrimitive(element, option, painter, widget)

    @staticmethod
    def _indicator_rect(rect: QRect, size: int = 18) -> QRect:
        side = min(size, rect.width(), rect.height())
        return QRect(
            rect.x() + (rect.width() - side) // 2,
            rect.y() + (rect.height() - side) // 2,
            side,
            side,
        )

    @staticmethod
    def _state(option):
        state = option.state
        enabled = bool(state & QStyle.StateFlag.State_Enabled)
        checked = bool(state & QStyle.StateFlag.State_On)
        hovered = bool(state & QStyle.StateFlag.State_MouseOver)
        return enabled, checked, hovered

    def _draw_checkbox(self, option, painter):
        enabled, checked, hovered = self._state(option)
        rect = self._indicator_rect(option.rect, 18).adjusted(1, 1, -1, -1)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if checked:
            fill = QColor("#21a8f3") if enabled else QColor("#5d7180")
            border = QColor("#21a8f3") if enabled else QColor("#5d7180")
        else:
            fill = QColor("#303030") if enabled else QColor("#292929")
            border = QColor("#aaaaaa") if hovered and enabled else QColor("#777777")

        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 4, 4)

        if checked:
            check_pen = QPen(
                QColor("#ffffff") if enabled else QColor("#d5d5d5"),
                2.1,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(check_pen)
            painter.drawLine(
                QPoint(rect.left() + 3, rect.center().y()),
                QPoint(rect.left() + 7, rect.bottom() - 4),
            )
            painter.drawLine(
                QPoint(rect.left() + 7, rect.bottom() - 4),
                QPoint(rect.right() - 3, rect.top() + 4),
            )
        painter.restore()

    def _draw_radio(self, option, painter):
        enabled, checked, hovered = self._state(option)
        rect = self._indicator_rect(option.rect, 18).adjusted(1, 1, -1, -1)
        center = rect.center()
        radius = max(1, rect.width() // 2 - 1)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if checked:
            border = QColor("#20a8f4") if enabled else QColor("#5d7180")
            inner = QColor("#20a8f4") if enabled else QColor("#5d7180")
        else:
            border = QColor("#aaaaaa") if hovered and enabled else QColor("#777777")
            inner = None

        painter.setPen(QPen(border, 1.8))
        painter.setBrush(QColor("#2d2d2d") if enabled else QColor("#292929"))
        painter.drawEllipse(center, radius, radius)
        if inner:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(inner)
            painter.drawEllipse(center, max(2, radius - 4), max(2, radius - 4))
        painter.restore()
