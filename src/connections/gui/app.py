"""Desktop entry point."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from connections.gui.window import MainWindow


def main(demo: bool = False) -> int:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Connections Studio")
    app.setOrganizationName("Connections Studio")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    if demo:
        window.load_demo()
    window.show()
    return app.exec()
