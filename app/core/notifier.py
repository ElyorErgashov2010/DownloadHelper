"""QSystemTrayIcon orqali tizim bildirishnomalari."""

from PySide6.QtWidgets import QSystemTrayIcon, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer


class Notifier:
    """Windows toast-bildirishnomalarini ko'rsatadi."""

    def __init__(self):
        self._tray: QSystemTrayIcon | None = None
        self._init_tray()

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
        self._tray.show()

    def notify(self, title: str, message: str, success: bool = True):
        """Bildirishnoma ko'rsatish."""
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
