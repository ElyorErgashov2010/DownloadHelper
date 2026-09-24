"""GUI ko'rinishi uchun yagona izchil tugma uslubi (QSS).

Barcha QPushButton elementlari (jumladan «Qayta tekshirish», yordam «?»
tugmalari va dialoglardagi tugmalar) bir xil qoramtir, ramkali ko'rinishda
bo'ladi. Scroll bar va progress bar bu yerda emas — ular mos ravishda
`slim_scrollbar.py` va `wave_progress_bar.py` da maxsus chiziladi.
"""

BUTTON_QSS = """
QPushButton {
    background-color: #353535;
    color: #e8e8e8;
    border: 1px solid #767676;
    border-radius: 4px;
    padding: 5px 12px;
}
QPushButton:hover {
    background-color: #454545;
    border-color: #21a8f3;
}
QPushButton:pressed {
    background-color: #2b2b2b;
}
QPushButton:disabled {
    color: #707070;
    border-color: #454545;
    background-color: #2f2f2f;
}
QPushButton:checked {
    background-color: #28547c;
    border-color: #66a9df;
}
"""
