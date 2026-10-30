"""A small, local design system; no downloaded fonts or assets."""

import re

from PySide6.QtGui import QColor, QPalette

COLORS = ["#F3D983", "#C5D9A3", "#AECBE5", "#D4BCE8"]
SOFT_COLORS = ["#FFFAE9", "#F3F8EA", "#F0F6FC", "#F8F1FC"]
DARK_GROUP_COLORS = ["#302B1D", "#233025", "#202D3E", "#30253E"]

STYLE = """
QWidget { color: #24283A; font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
          font-size: 14px; }
QMainWindow, QWidget#Root, QScrollArea, QWidget#Page { background: #F7F7F2; }
QScrollArea { border: none; }
QFrame#Sidebar { background: #EFEFE8; border-right: 1px solid #DDDFD5; }
QLabel { background: transparent; }
QLabel#Brand { font-size: 21px; font-weight: 700; letter-spacing: -0.5px; }
QLabel#BrandSub { font-size: 10px; letter-spacing: 2.4px; color: #707568; }
QLabel#Eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 1.9px; color: #74796F; }
QLabel#Hero { font-family: Georgia, 'Times New Roman', serif; font-size: 43px;
             letter-spacing: -1.7px; color: #292D39; }
QLabel#Subtitle { color: #74796F; font-size: 14px; }
QLabel#CardTitle { font-size: 19px; font-weight: 650; letter-spacing: -0.3px; }
QLabel#Muted { color: #767B72; font-size: 12px; }
QLabel#Pill { background: #E8ECDF; color: #4E6353; border-radius: 12px;
             padding: 6px 12px; font-size: 11px; font-weight: 650; }
QLabel#Message { background: #EDE9F8; border: 1px solid #DDD4EE; border-radius: 10px;
                color: #51416D; padding: 12px 16px; }
QFrame#Card { background: #FFFFFF; border: 1px solid #E1E4D9; border-radius: 18px; }
QFrame#Tip { background: #EAF0E8; border-radius: 12px; }
QPushButton { background: white; border: 1px solid #DDDFD6; border-radius: 9px;
              padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #F1F0F7; border-color: #B5A9D1; }
QPushButton:pressed { background: #E3DCEE; }
QPushButton:disabled { color: #9A9D95; background: #F0F1EB; border-color: #E3E5DC; }
QPushButton#Primary { background: #6950A1; color: white; border: none; padding: 14px 22px; }
QPushButton#Primary:hover { background: #59418E; }
QPushButton#Primary:pressed { background: #493475; }
QPushButton#Primary:disabled { background: #E6E1ED; color: #9C91AE; }
QPushButton#Ghost { background: transparent; border: none; color: #6D6087; padding: 8px 10px; }
QPushButton#Ghost:hover { background: #E8E3EF; }
QPushButton#Nav { background: transparent; border: none; text-align: left; color: #7B7F74;
                 padding: 13px 14px; font-weight: 500; }
QPushButton#Nav:checked { background: #E0DCE9; color: #59417E; font-weight: 650; }
QPushButton#Nav:hover { background: #E5E6DC; }
QPushButton#Small { padding: 7px 11px; font-size: 12px; background: transparent; }
QPushButton#Small:checked { background: #303848; color: white; border-color: #303848; }
QPushButton#FeedbackCorrect, QPushButton#FeedbackIncorrect {
    min-width: 100px; padding: 10px 14px; font-weight: 700; border-width: 2px;
}
QPushButton#FeedbackCorrect { background: #F2FAF3; color: #27643A; border-color: #8CB69A; }
QPushButton#FeedbackCorrect:hover { background: #DDEFE1; }
QPushButton#FeedbackCorrect:checked { background: #27643A; color: white; border-color: #27643A; }
QPushButton#FeedbackIncorrect { background: #FFF5F3; color: #9A3732; border-color: #D9A19A; }
QPushButton#FeedbackIncorrect:hover { background: #F9DFDA; }
QPushButton#FeedbackIncorrect:checked { background: #A43D36; color: white; border-color: #A43D36; }
QPushButton#FeedbackCorrect:disabled, QPushButton#FeedbackIncorrect:disabled {
    background: #F0F1EB; color: #92988D; border-color: #DEE2D7;
}
QLabel#ConfirmedStatus { color: #27643A; font-weight: 700; font-size: 12px; }
QLabel#GroupWords { font-size:13px; font-weight:700; color:#363D39; }
QLabel#GroupExplanation { color:#62695F; font-size:12px; }
QLabel#SidebarQuote { font-family:Georgia; font-size:21px; color:#777E6E; }
QLineEdit { border: 1px solid #DDE0D7; background: #FCFCF9; border-radius: 10px;
            padding: 10px; selection-background-color: #6950A1; }
QLineEdit:focus { border: 2px solid #9277BC; background: #FFFFFF; }
QLineEdit#Word { background: #F3F4EE; border: 1px solid #E7E9E0;
                font-size: 13px; font-weight: 650; border-radius: 10px; padding: 5px; }
QLineEdit#Word:focus { border: 2px solid #9277BC; background: #FAF7FF; }
QComboBox { background: white; border: 1px solid #DDDFD6; border-radius: 9px;
            padding: 9px 12px; min-width: 140px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #E4DDEF;
                            selection-color: #302241; padding: 6px; }
QDialog { background: #F7F7F2; }
QDialog#CenteredDialog { border: 2px solid #DDD4EE; border-radius: 16px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px;
                       border: 1px solid #AAA99F; background: white; }
QCheckBox::indicator:checked { background: #6950A1; border: 3px solid #D7CDE9; }
QCheckBox::indicator:disabled { background: #E9EAE4; border-color: #D4D6CE; }
QTextEdit { background: white; border: 1px solid #DDDFD6; border-radius: 10px; padding: 8px; }
QProgressBar { background: #E9E6EF; border: none; border-radius: 2px; max-height: 4px; }
QProgressBar::chunk { background: #8E78B7; border-radius: 2px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #CBCDCA; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #303444; color: white; padding: 8px; border: none; }
"""

# Semantic equivalents preserve contrast while sharing layout and typography.
DARK_COLORS = {
    "#24283A": "#E5EAF3",
    "#F7F7F2": "#141A24",
    "#EFEFE8": "#101620",
    "#DDDFD5": "#303A49",
    "#707568": "#A0ACBE",
    "#74796F": "#A7B2C4",
    "#292D39": "#F0F3FA",
    "#767B72": "#A9B4C5",
    "#E8ECDF": "#24382C",
    "#4E6353": "#B6D8BE",
    "#EDE9F8": "#29243E",
    "#DDD4EE": "#514469",
    "#51416D": "#D9C9F5",
    "#FFFFFF": "#1C2431",
    "#E1E4D9": "#344052",
    "#EAF0E8": "#203029",
    "#DDDFD6": "#3D485A",
    "#F1F0F7": "#303449",
    "#B5A9D1": "#9C84C7",
    "#E3DCEE": "#3E3453",
    "#9A9D95": "#8390A4",
    "#F0F1EB": "#232B37",
    "#E3E5DC": "#303B4D",
    "#6950A1": "#8464BD",
    "#59418E": "#9775D0",
    "#493475": "#6C4D9D",
    "#E6E1ED": "#353044",
    "#9C91AE": "#9C90AE",
    "#6D6087": "#BDA5DF",
    "#E8E3EF": "#332D43",
    "#7B7F74": "#A8B4C7",
    "#E0DCE9": "#332D47",
    "#59417E": "#D2B8F5",
    "#E5E6DC": "#263041",
    "#303848": "#4A3C60",
    "#F2FAF3": "#1F3428",
    "#27643A": "#88D9A0",
    "#8CB69A": "#427552",
    "#DDEFE1": "#294C36",
    "#FFF5F3": "#3C2629",
    "#9A3732": "#F1A29D",
    "#D9A19A": "#935550",
    "#F9DFDA": "#543034",
    "#A43D36": "#9A403C",
    "#DEE2D7": "#354051",
    "#92988D": "#93A0B3",
    "#DDE0D7": "#384557",
    "#FCFCF9": "#18212D",
    "#9277BC": "#BA9AE5",
    "#F3F4EE": "#222D3C",
    "#E7E9E0": "#364256",
    "#FAF7FF": "#2E2940",
    "#E4DDEF": "#443555",
    "#302241": "#F0E7FC",
    "#AAA99F": "#718096",
    "#D7CDE9": "#624E7E",
    "#E9EAE4": "#293442",
    "#D4D6CE": "#3B495A",
    "#E9E6EF": "#343044",
    "#8E78B7": "#B99BDD",
    "#CBCDCA": "#536079",
    "#303444": "#283349",
    "#363D39": "#E4EAF3",
    "#62695F": "#B3BECD",
    "#777E6E": "#9CAAC0",
}


def style_for(theme: str) -> str:
    if theme != "dark":
        return STYLE
    style = re.sub(r"#[0-9A-Fa-f]{6}", lambda match: DARK_COLORS.get(match[0], match[0]), STYLE)
    style = style.replace("background: white", "background: #1C2431")
    # Selected success retains a dark green fill and a white label.
    return style + "\nQPushButton#FeedbackCorrect:checked { background:#286241; color:white; }"


def palette_for(theme: str) -> QPalette:
    palette = QPalette()
    if theme == "dark":
        for role, color in (
            (QPalette.ColorRole.Window, "#141A24"),
            (QPalette.ColorRole.Base, "#1C2431"),
            (QPalette.ColorRole.WindowText, "#E5EAF3"),
            (QPalette.ColorRole.Text, "#E5EAF3"),
            (QPalette.ColorRole.Button, "#222D3C"),
            (QPalette.ColorRole.ButtonText, "#E5EAF3"),
            (QPalette.ColorRole.Highlight, "#8464BD"),
            (QPalette.ColorRole.HighlightedText, "#FFFFFF"),
            (QPalette.ColorRole.PlaceholderText, "#8F9CAF"),
        ):
            palette.setColor(role, QColor(color))
    return palette
