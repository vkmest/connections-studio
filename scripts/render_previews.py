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
    window.apply_theme("light", persist=False)
    window.set_sidebar_collapsed(False, persist=False)
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
    window.resize(1320, 900)
    window.apply_theme("dark", persist=False)
    dark_settings = SettingsDialog(Settings(), window)
    dark_settings.show()
    app.processEvents()
    dark_settings.grab().save(str(output / "settings-dark.png"))
    dark_settings.close()
    app.processEvents()
    window.grab().save(str(output / "connections-dark.png"))
    for index in range(4):
        window.toggle_lock(index, True)
    app.processEvents()
    window.grab().save(str(output / "completed-dark.png"))
    window.new_puzzle()
    window.set_sidebar_collapsed(True, persist=False)
    app.processEvents()
    window.grab().save(str(output / "workspace-dark.png"))
    window.capture_prompt.note.setText(
        "Read the screenshot, then review and edit the tiles. Runs locally with Ollama."
    )
    window.capture_prompt.show()
    app.processEvents()
    window.capture_prompt.grab().save(str(output / "capture-prompt.png"))
    window.capture_prompt.hide()
    window.busy_dialog.status.setText("Looking for connections… Checking meanings and wordplay.")
    window.busy_dialog.note.setText("Extended allows up to five minutes per request.")
    window.busy_dialog.show()
    app.processEvents()
    window.busy_dialog.grab().save(str(output / "loading.png"))
    window.busy_dialog.hide()
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
