"""Centered, nonblocking dialogs for the next action and in-flight work."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QProgressBar, QVBoxLayout

from connections.gui.widgets import GridMark, button, label


class CenteredDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setObjectName("CenteredDialog")
        self.setFixedWidth(460)

    def recenter(self):
        center = self.parentWidget().mapToGlobal(self.parentWidget().rect().center())
        self.move(center - self.rect().center())

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        self.recenter()


class CapturePrompt(CenteredDialog):
    read_requested = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Screenshot ready")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 28)
        layout.setSpacing(18)
        layout.addWidget(GridMark(34))
        layout.addWidget(label("Screenshot ready.", "CardTitle"))
        layout.addWidget(label("Next, read the 16 words.", "Subtitle"))
        self.note = label("", "Muted", wrap=True)
        layout.addWidget(self.note)
        self.read_button = button("Read words from image  →", "Primary", self.start_read)
        self.read_button.setDefault(True)
        layout.addWidget(self.read_button)
        layout.addWidget(button("Not now", "Ghost", self.reject))

    def start_read(self):
        self.accept()
        self.read_requested.emit()


class BusyDialog(CenteredDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Working on your puzzle")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        top = QHBoxLayout()
        top.addWidget(GridMark(34))
        top.addWidget(label("A little thinking space.", "CardTitle"))
        layout.addLayout(top)
        self.status = label("", "Subtitle", wrap=True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        self.note = label("", "Muted", wrap=True)
        layout.addWidget(self.note)

    def reject(self):
        # Escape must not imply a network request has been cancelled.
        pass

    def closeEvent(self, event):
        event.ignore()
