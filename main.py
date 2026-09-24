"""Download Helper - N_m3u8DL-RE uchun GUI va headless CLI o'rami."""

import sys


def _apply_gui_style(app):
    """Barcha tugmalar uchun yagona izchil qoramtir ko'rinish."""
    from app.theme import BUTTON_QSS
    app.setStyleSheet(BUTTON_QSS)


def main():
    argv = sys.argv[1:]

    # Headless (GUI'siz) rejim: bot yoki skript chaqirig'i
    if "--run" in argv:
        from app.cli_runner import run_cli
        sys.exit(run_cli(argv))

    # Oddiy GUI rejim. Windows o'zining native light/dark dizaynini ishlatadi.
    from PySide6.QtWidgets import QApplication

    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Download Helper")
    _apply_gui_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
