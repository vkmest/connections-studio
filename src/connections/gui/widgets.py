"""Reusable presentation widgets with no API or puzzle state."""

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from connections.gui.theme import COLORS, SOFT_COLORS
from connections.models import Group


def label(text: str, role: str = "", *, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setObjectName(role)
    widget.setWordWrap(wrap)
    return widget


def button(text: str, role: str = "", callback=None) -> QPushButton:
    widget = QPushButton(text)
    widget.setObjectName(role)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:
        widget.clicked.connect(callback)
    return widget


class GridMark(QWidget):
    def __init__(self, size=34):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        cell = (self.width() - 4) / 2
        for index, color in enumerate(COLORS):
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(
                QRectF((index % 2) * (cell + 4), (index // 2) * (cell + 4), cell, cell), 5, 5
            )


class CapturePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(238)
        self.pixmap = QPixmap()
        self.setAccessibleName("Screenshot preview")

    def set_image(self, data: bytes | None):
        self.pixmap = QPixmap()
        if data:
            self.pixmap.loadFromData(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setBrush(QColor("#F7F7F2"))
        painter.setPen(QPen(QColor("#D5DACC"), 1, Qt.PenStyle.DashLine))
        painter.drawRoundedRect(box, 13, 13)
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.size() - QSize(28, 28),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(
                (self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled
            )
            return
        painter.translate(self.width() / 2, self.height() / 2 - 4)
        painter.rotate(-7)
        painter.setPen(Qt.PenStyle.NoPen)
        words = ["FIND", "THE", "HIDDEN", "THREAD", "16", "WORDS", "4", "GROUPS"]
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for row in range(4):
            for col in range(4):
                tile = QRectF(-132 + col * 67, -89 + row * 45, 61, 39)
                painter.setBrush(QColor(COLORS[row] if row == 1 else "#E8EAE1"))
                painter.drawRoundedRect(tile, 6, 6)
                painter.setPen(QColor("#454D43" if row < 2 else "#A8AEA1"))
                painter.drawText(
                    tile, Qt.AlignmentFlag.AlignCenter, words[row * 4 + col] if row < 2 else "·"
                )
                painter.setPen(Qt.PenStyle.NoPen)


class GroupCard(QFrame):
    lock_changed = Signal(int, bool)
    reject_changed = Signal(int)

    def __init__(self, group: Group, index: int, locked: bool, rejected: bool):
        super().__init__()
        self.setObjectName("GroupCard")
        self.setStyleSheet(
            f"QFrame#GroupCard {{background:{SOFT_COLORS[index]};"
            f"border:1px solid {COLORS[index]};border-radius:16px;}}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(23, 18, 23, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        number = label(f"0{index + 1}  /  SUGGESTED GROUP", "Eyebrow")
        number.setStyleSheet("font-size:10px;letter-spacing:1.3px;color:#666D60;")
        top.addWidget(number)
        top.addStretch()
        top.addWidget(label(group.confidence.capitalize() + " confidence", "Muted"))
        layout.addLayout(top)
        title = label(group.title, "CardTitle", wrap=True)
        layout.addWidget(title)
        words = label("   ·   ".join(group.words), wrap=True)
        words.setStyleSheet("font-size:13px;font-weight:700;color:#363D39;")
        words.setMinimumHeight(32)
        layout.addWidget(words)
        explanation = label(group.explanation, "Subtitle", wrap=True)
        explanation.setStyleSheet("color:#62695F;font-size:12px;")
        layout.addWidget(explanation)
        layout.addStretch()
        actions = QHBoxLayout()
        self.lock_button = button("Confirmed" if locked else "Mark correct", "Small")
        self.lock_button.setCheckable(True)
        self.lock_button.setChecked(locked)
        self.lock_button.setEnabled(not rejected)
        self.lock_button.setToolTip("Lock this group after the game accepts it.")
        self.lock_button.toggled.connect(lambda checked: self.lock_changed.emit(index, checked))
        self.reject_button = button("Undo rejection" if rejected else "Not a match", "Ghost")
        self.reject_button.setEnabled(not locked)
        self.reject_button.setToolTip("Exclude these exact four words from the next solve.")
        self.reject_button.clicked.connect(lambda: self.reject_changed.emit(index))
        actions.addWidget(self.lock_button)
        actions.addStretch()
        actions.addWidget(self.reject_button)
        layout.addLayout(actions)
