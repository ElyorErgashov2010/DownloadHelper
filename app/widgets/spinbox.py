"""Aniq ▲/▼ uchburchakli QSpinBox.

Windows 11 (`windows11` QStyle) QSpinBox tugmalarini mayda chevron belgilari
bilan chizadi, QSS 'border' usulidagi uchburchaklar esa u yerda ko'pincha
quvvatli kvadrat bo'lib chiqadi. Bu modul uchburchaklarni to'g'ridan-to'g'ri
kod bilan chizadi:

- Yuqori tugma: ▲, pastki tugma: ▼.
- Sichqoncha tugma ustida turganda uchburchak oqaradi.
- Bosib turilganda qiymat auto-repeat bilan o'zgarib turadi (QSpinBox'ning
  standart tugma takrorlash mexanizmi).
"""

from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QBrush, QColor, QCursor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSpinBox, QStyle, QStyleOptionSpinBox

_SPINBOX_QSS = """
QSpinBox {
    background: #2b2b2b;
    color: #e8e8e8;
    border: 1px solid #767676;
    border-radius: 4px;
    padding: 3px 6px;
    min-width: 64px;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border: none;
    border-left: 1px solid #767676;
    border-bottom: 1px solid #767676;
    border-top-right-radius: 3px;
    background: #353535;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border: none;
    border-left: 1px solid #767676;
    border-bottom-right-radius: 3px;
    background: #353535;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #454545;
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background: #2f2f2f;
}
/* Arrow'lar o'lchami 0 — bularni biz o'zimiz chizamiz (kvadrat chiqmaydi). */
QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 0;
    height: 0;
}
"""


class ArrowSpinBox(QSpinBox):
    """O'ng tomonidagi ▲/▼ tugmalari aniq uchburchakli QSpinBox."""

    _BTN_WIDTH = 22.0   # QSS dagi up/down button kengligi bilan bir xil
    _ARROW_HALF_W = 4.5
    _ARROW_H = 6.0

    def __init__(self, parent=None):
        super().__init__(parent)
        # Yuqoridagi/pastki tugma uchun yetarli balandlik.
        self.setMinimumHeight(30)
        self.setStyleSheet(_SPINBOX_QSS)
        # Bosib turilganda qiymat takrorlanishi uchun tezlashtirilgan rejim.
        self.setAccelerated(True)
        self.setKeyboardTracking(True)

    # ── Geometriya ───────────────────────────────────────────────

    def _button_rect(self, up: bool) -> QRect:
        """▲ yoki ▼ tugmasining ekrandagi to'liq tuzilishi (QSS hisobga olinadi)."""
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        sub = QStyle.SubControl.SC_SpinBoxUp if up else QStyle.SubControl.SC_SpinBoxDown
        rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox, opt, sub, self
        )
        if rect.isNull() or rect.width() < 6 or rect.height() < 6:
            # QSS geometriyasi qo'llanib bo'lmagani — o'ng 22px ni yarimlab hisoblaymiz.
            h = max(6, self.height() // 2)
            x = self.width() - int(self._BTN_WIDTH)
            rect = QRect(x, 1 if up else self.height() - h - 1,
                         int(self._BTN_WIDTH), h)
        return rect

    # ── Chizish ──────────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        mouse_pos = self.mapFromGlobal(QCursor.pos())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for up in (True, False):
            rect = self._button_rect(up)
            hovered = rect.contains(mouse_pos)
            color = QColor("#ffffff") if hovered else QColor("#d0d0d0")
            cx = rect.center().x() + 0.5
            cy = rect.center().y() + 0.5
            hw, ah = self._ARROW_HALF_W, self._ARROW_H
            if up:
                poly = QPolygonF([
                    QPointF(cx, cy - ah / 2),
                    QPointF(cx - hw, cy + ah / 2),
                    QPointF(cx + hw, cy + ah / 2),
                ])
            else:
                poly = QPolygonF([
                    QPointF(cx, cy + ah / 2),
                    QPointF(cx - hw, cy - ah / 2),
                    QPointF(cx + hw, cy - ah / 2),
                ])
            painter.setPen(QPen(color, 1.0))
            painter.setBrush(QBrush(color))
            painter.drawPolygon(poly)
        painter.end()
