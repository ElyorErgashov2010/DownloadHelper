"""Download Helper - N_m3u8DL-RE uchun GUI va headless CLI o'rami."""

import sys


def main():
    argv = sys.argv[1:]

    # Headless (GUI'siz) rejim: bot yoki skript chaqirig'i
    if "--run" in argv:
        from app.cli_runner import run_cli
        sys.exit(run_cli(argv))

    # Oddiy GUI rejim
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication

    from app.main_window import MainWindow
    from app.widgets.selection_indicator_style import SelectionIndicatorStyle

    app = QApplication(sys.argv)
    # Fusion style progress/spinbox'ni izchil chizadi, custom proxy esa eski
    # dizaynga o'xshash radio va checkbox indikatorlarini saqlaydi.
    app.setStyle(SelectionIndicatorStyle("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#252525"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#303030"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#383838"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#404040"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#287abd"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#303030"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9a9a9a"))
    app.setPalette(palette)
    app.setApplicationName("Download Helper")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
