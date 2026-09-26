"""Download Helper - N_m3u8DL-RE uchun GUI va headless CLI o'rami."""

import os
import sys
import traceback


def _error_log_path():
    """Exe yonidagi xato kundaligi faylining yo'li."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base, "DownloadHelper-error.log")


def _install_error_log():
    """Kutilmagan xatolarni faylga yozib boradi.

    Windowed (oynali) rejimda xato matni ekranga chiqmaydi, shuning uchun
    ilova ochilmasa sababini ko'rish uchun uni yonidagi faylga yozamiz.
    """

    def _excepthook(exc_type, exc_value, exc_tb):
        try:
            lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            with open(_error_log_path(), "a", encoding="utf-8") as f:
                f.write("".join(lines) + "\n" + "=" * 60 + "\n")
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook


_SINGLE_INSTANCE_KEY = "DownloadHelper_SingleInstance_v1"


def _acquire_single_instance(app):
    """Faqat bitta GUI jarayoni ishlashini kafolatlaydi.

    Agar ilova allaqachon ishlayotgan bo'lsa, mavjud instansiyaga «show»
    yozuvi yuboriladi (u asosiy oynani oldinga chiqaradi) va None qaytariladi
    — yangi jarayon darhol chiqishi kerak.

    Aks holda boshqa bosilishlar uchun QLocalServer ochiladi va server
    qaytariladi. Server `app` ga bog'lab saqlanadi (jonli qolishi uchun).
    """
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QMainWindow

    client = QLocalSocket()
    client.connectToServer(_SINGLE_INSTANCE_KEY)
    if client.waitForConnected(300):
        # Mavjud instansiya ishlayapti — unga «oynani ko'rsat» signal yuboramiz.
        try:
            client.write(b"show")
            client.flush()
            client.waitForBytesWritten(300)
        finally:
            client.disconnectFromServer()
        return None

    # Server yo'q — biz birinchi instansiya.
    server = QLocalServer(app)
    QLocalServer.removeServer(_SINGLE_INSTANCE_KEY)

    def _on_new_connection():
        conn = server.nextPendingConnection()
        if conn is None:
            return

        def _read_signal():
            if b"show" not in conn.readAll().data():
                return
            for w in app.topLevelWidgets():
                if isinstance(w, QMainWindow) and w.isVisible():
                    w.showNormal()
                    w.raise_()
                    w.activateWindow()
                    break

        conn.readyRead.connect(_read_signal)
        conn.disconnected.connect(conn.deleteLater)

    server.newConnection.connect(_on_new_connection)
    # Server `app` ga bog'lab saqlanadi — jonli qolishi shart.
    app._single_instance_server = server
    if not server.listen(_SINGLE_INSTANCE_KEY):
        # Nadir holat (masalan, ikki bosish shu paytda): ochilishni blok
        # qilmaymiz, faqat keyingi «show» signallarini ololmaymiz.
        pass
    return server


def main():
    argv = sys.argv[1:]

    # Headless (GUI'siz) rejim: bot yoki skript chaqirig'i — bu yerda
    # yagona instansiya qoidalari qo'llanmaydi (serverlarni qo'ng'iroq qiladi).
    if "--run" in argv:
        from app.cli_runner import run_cli
        sys.exit(run_cli(argv))

    # Oddiy GUI rejim. Windows o'zining native light/dark dizaynini
    # ishlatadi — tugmalar native (fix/windows-ui-and-scroll uslubi).
    _install_error_log()

    from PySide6.QtWidgets import QApplication

    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Download Helper")

    # Ilova allaqachon ochiq bo'lsa — mavjud oynani oldinga chiqarib,
    # ikkinchi jarayonni o'chiramiz.
    if _acquire_single_instance(app) is None:
        sys.exit(0)

    window = MainWindow()
    window.show()
    # Oyna ba'zan ekran chetida yoki minimallashtirilgan qoladi — bu uni
    # oldingi planga olib chiqadi.
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
