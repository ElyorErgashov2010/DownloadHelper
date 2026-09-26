"""QSystemTrayIcon orqali tizim bildirishnomalari va tray ikonkasi.

Tray ikonka xulqi:
- Chap bosish — asosiy oynani oldinga olib chiqadi.
- O'ng bosish — kontekst menyu: «Oynani ochish» / «Ochirish».
"""

from PySide6.QtWidgets import (
    QMenu, QSystemTrayIcon, QApplication,
)
from PySide6.QtGui import QIcon


class Notifier:
    """Windows toast-bildirishnomalari va tray ikonka boshqaruvi."""

    def __init__(self):
        self._tray: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None
        self._window = None
        self._init_tray()

    def set_window(self, window):
        """Asosiy oynani eslab qoladi — tray ikonkaga bosilganda ishlatiladi."""
        self._window = window

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon()
        # Agar bo'lsa, dastur ikonkasini ishlatamiz
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self._tray.setIcon(app.windowIcon())
        else:
            # Standart ikonka
            self._tray.setIcon(
                app.style().standardIcon(app.style().StandardPixmap.SP_ArrowDown)
                if app else QIcon()
            )
        self._tray.setToolTip("Download Helper")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray_menu = self._build_menu()
        self._tray.setContextMenu(self._tray_menu)
        self._tray.show()

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        show_action = menu.addAction("Oynani ochish")
        show_action.triggered.connect(self.show_window)
        menu.addSeparator()
        quit_action = menu.addAction("Ochirish")
        quit_action.triggered.connect(self.quit_app)
        return menu

    def _on_tray_activated(self, reason):
        # Yagona chap bosish (Trigger) — oynani oldinga chiqaramiz.
        # O'ng bosish (Context) — Windows o'zi kontekst menyuni ochadi.
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        """Asosiy oynani ko'rsatadi va oldinga olib chiqadi."""
        if self._window is not None:
            self._window.showNormal()
            self._window.raise_()
            self._window.activateWindow()

    def quit_app(self):
        """Ilovaning to'liq ochilishi (jarayon ham tugaydi)."""
        if self._window is not None:
            self._window.close()
        else:
            QApplication.quit()

    def notify(self, title: str, message: str, success: bool = True):
        """Bildirishnoma ko'rsatadi."""
        if not self._tray:
            return
        icon = (
            QSystemTrayIcon.MessageIcon.Information if success
            else QSystemTrayIcon.MessageIcon.Warning
        )
        self._tray.showMessage(title, message, icon, 5000)

    def cleanup(self):
        if self._tray:
            self._tray.hide()
            self._tray = None
            self._tray_menu = None
