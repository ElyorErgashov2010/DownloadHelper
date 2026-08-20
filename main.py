"""Download Helper - N_m3u8DL-RE uchun GUI va headless CLI o'rami."""

import sys


def main():
    argv = sys.argv[1:]

    # Headless (GUI'siz) rejim: bot yoki skript chaqirig'i
    if "--run" in argv:
        from app.cli_runner import run_cli
        sys.exit(run_cli(argv))

    # Oddiy GUI rejim
    from PySide6.QtWidgets import QApplication

    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Download Helper")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
