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


def main():
    argv = sys.argv[1:]

    # Headless (GUI'siz) rejim: bot yoki skript chaqirig'i
    if "--run" in argv:
        from app.cli_runner import run_cli
        sys.exit(run_cli(argv))

    # Oddiy GUI rejim. Windows o'zining native light/dark dizaynini ishlatadi.
    _install_error_log()

    from PySide6.QtWidgets import QApplication

    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Download Helper")
    window = MainWindow()
    window.show()
    # Oyna ba'zan ekran chetida yoki minimallashtirilgan qoladi — bu uni
    # oldingi planga olib chiqadi.
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
