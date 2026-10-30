"""Render real widgets and an original sample puzzle for docs (no network calls)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from connections.config import Settings
from connections.demo import DEMO_WORDS
from connections.gui.settings_dialog import SettingsDialog
from connections.gui.window import MainWindow
from connections.service import SolverService


def main():
    output = Path(__file__).resolve().parents[1] / "docs" / "images"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow(SolverService(Settings()))
    window.show()
    app.processEvents()
    window.grab().save(str(output / "workspace.png"))
    window.load_demo()
    app.processEvents()
    window.grab().save(str(output / "review.png"))
    window.start_solve()
    app.processEvents()
    window.grab().save(str(output / "connections.png"))
    window.toggle_lock(0, True)
    window.toggle_rejection(1)
    app.processEvents()
    window.grab().save(str(output / "feedback.png"))
    window.reset_feedback()
    window.resize(1060, 740)
    app.processEvents()
    window.grab().save(str(output / "compact.png"))
    settings = SettingsDialog(Settings(), window)
    settings.show()
    app.processEvents()
    settings.grab().save(str(output / "settings.png"))
    settings.close()
    window.close()

    sample = Image.new("RGB", (840, 560), "#FAFAF6")
    draw = ImageDraw.Draw(sample)
    try:
        font = ImageFont.truetype("arialbd.ttf", 26)
    except OSError:
        font = ImageFont.load_default(size=26)
    for index, word in enumerate(DEMO_WORDS):
        x, y = 20 + (index % 4) * 205, 20 + (index // 4) * 135
        draw.rounded_rectangle((x, y, x + 185, y + 115), radius=12, fill="#EBEDE4")
        draw.text((x + 92, y + 57), word, fill="#252B27", font=font, anchor="mm")
    examples = output.parents[1] / "examples"
    examples.mkdir(exist_ok=True)
    sample.save(examples / "practice-grid.png")
    (examples / "words.txt").write_text("\n".join(DEMO_WORDS) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
