"""QSpinBox uchun aniq ▲/▼ tugmalar patch'i.

Windows 11 (`windows11` QStyle) QSpinBox tugmalarini mayda Segoe Fluent
chevron belgilari bilan chizadi va o'qlar juda noqulay ko'rinadi.
Bu modul spinbox'ga klassik, ustma-ust turgan aniq ▲/▼ ko'rinishini beradi:

- Yuqori tugma: ▲, pastki tugma: ▼.
- Bosib turilganda qiymat auto-repeat bilan o'zgarib turadi (QSpinBox'ning
  standart tugma takrorlash mexanizmi ishlaydi).
"""

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
QSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid #d0d0d0;
    background: transparent;
}
QSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #d0d0d0;
    background: transparent;
}
QSpinBox::up-arrow:hover, QSpinBox::down-arrow:hover {
    border-bottom-color: #ffffff;
    border-top-color: #ffffff;
}
"""


class SpinBoxFocusToBottom:
    """Klassik, aniq ko'rinadigan ▲/▼ tugmalarni qaytaruvchi spinbox patch'i.

    Foydalanish::

        from app.widgets.spinbox import SpinBoxFocusToBottom
        SpinBoxFocusToBottom.patch(spinbox)
    """

    @classmethod
    def patch(cls, spinbox) -> None:
        """`spinbox`ga aniq ▲/▼ tugmalar ko'rinishini qo'llaydi."""
        # Yuqoridagi/pastki tugma uchun yetarli balandlik.
        spinbox.setMinimumHeight(30)
        spinbox.setStyleSheet(_SPINBOX_QSS)
        # Bosib turilganda qiymat takrorlanishi uchun tezlashtirilgan rejim.
        spinbox.setAccelerated(True)
        spinbox.setKeyboardTracking(True)
