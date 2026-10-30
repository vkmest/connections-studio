import io

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from connections.config import Settings
from connections.demo import DEMO_WORDS, demo_solution
from connections.gui.widgets import GroupCard
from connections.gui.window import MainWindow
from connections.models import Usage
from connections.service import OperationResult, ServiceError, SolverService


def window(qtbot):
    widget = MainWindow(service=SolverService(Settings(api_key="")))
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_demo_and_edits_clear_results_and_constraints(qtbot):
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    assert len(widget.solution.groups) == 4
    widget.toggle_lock(0, True)
    assert len(widget.locked) == 1
    widget.show_workspace()
    widget.word_inputs[0].setFocus()
    widget.word_inputs[0].selectAll()
    qtbot.keyClicks(widget.word_inputs[0], "NEW WORD")
    assert widget.solution is None
    assert not widget.locked and not widget.rejected
    assert not widget.demo_mode


def test_paste_image_previews_without_api_call(qtbot):
    widget = window(qtbot)
    image = QImage(300, 300, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    QApplication.clipboard().setImage(image)
    widget.paste_clipboard()
    assert widget.prepared_image is not None
    assert not widget.busy
    assert widget.solution is None
    assert widget.extract_button.isEnabled()


def test_paste_words_preserves_phrases(qtbot):
    widget = window(qtbot)
    QApplication.clipboard().setText("\n".join(["ICE CREAM", *DEMO_WORDS[1:]]))
    widget.paste_clipboard()
    assert widget.word_inputs[0].text() == "ICE CREAM"
    assert widget.solve_button.isEnabled()


def test_new_image_clears_stale_words(qtbot):
    widget = window(qtbot)
    widget.load_demo()
    stream = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(stream, "PNG")
    widget.set_image(stream.getvalue())
    assert all(not field.text() for field in widget.word_inputs)
    assert not widget.solve_button.isEnabled()


def test_background_error_restores_controls(qtbot, monkeypatch):
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)

    def fail(request):
        raise ServiceError("Test network failure")

    monkeypatch.setattr(widget.service, "solve", fail)
    widget.start_solve()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert "Test network failure" in widget.message_label.text()
    assert widget.solve_button.isEnabled()
    assert widget.solution is None


def test_background_success_displays_solution(qtbot, monkeypatch):
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)
    monkeypatch.setattr(
        widget.service,
        "solve",
        lambda request: OperationResult(
            demo_solution(), Usage(input_tokens=100, estimated_cost_usd=0.001)
        ),
    )
    widget.start_solve()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert len(widget.solution.groups) == 4
    assert widget.session_cost == 0.001


def test_bulk_paste_never_silently_truncates_entries(qtbot):
    widget = window(qtbot)
    widget.load_demo()
    QApplication.clipboard().setText("\n".join(["X" * 81, *DEMO_WORDS[1:]]))
    widget.paste_clipboard()
    assert widget.word_inputs[0].text() == "BASS"
    assert "80" in widget.message_label.text()


def test_close_is_deferred_while_request_runs(qtbot, monkeypatch):
    from threading import Event

    release = Event()
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)

    def slow(request):
        release.wait(timeout=2)
        return OperationResult(demo_solution(), Usage())

    monkeypatch.setattr(widget.service, "solve", slow)
    widget.start_solve()
    try:
        assert not widget.close()
        assert widget.isVisible()
        assert widget.busy
    finally:
        release.set()
        qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert widget.close()


def test_invalid_environment_opens_recovery_ui_without_loading_credentials(qtbot, monkeypatch):
    from connections.config import Settings
    from connections.gui.window import MainWindow

    def invalid():
        raise ValueError("Unknown CONNECTIONS_PROVIDER. Use openai, kimi, deepseek or ollama.")

    monkeypatch.setattr(Settings, "from_environment", invalid)
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.service.settings.api_key == ""
    assert "CONNECTIONS_PROVIDER" in window.message_label.text()
    assert "Settings" in window.message_label.text()


def test_rethink_consumes_feedback_and_never_displays_failed_old_suggestions(qtbot, monkeypatch):
    from threading import Event

    release = Event()
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    widget.demo_mode = False
    widget.toggle_lock(0, True)
    widget.toggle_lock(1, True)
    widget.toggle_rejection(2)
    widget.toggle_rejection(3)
    captured = []

    def fail(request, *, fresh=False):
        assert fresh
        captured.append(request)
        release.wait(timeout=3)
        raise ServiceError("The answer repeated a rejected group.")

    monkeypatch.setattr(widget.service, "solve", fail)
    widget.start_solve()
    try:
        assert len(widget.findChildren(GroupCard)) >= 2
        cards = [widget.group_grid.itemAt(i).widget() for i in range(widget.group_grid.count())]
        cards = [card for card in cards if isinstance(card, GroupCard)]
        assert len(cards) == 2
        assert all(not card.lock_button.isChecked() for card in cards)
        assert all(not card.reject_button.isChecked() for card in cards)
    finally:
        release.set()
        qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert len(captured[0].locked) == 2
    assert len(captured[0].rejected) == 2
    assert "No new answer" in widget.message_label.text()
    assert "previous" in widget.results_subtitle.text().lower()
    assert len(widget.locked) == 2 and len(widget.rejected) == 2
    assert not widget.copy_button.isEnabled()
    assert not widget.export_button.isEnabled()
    card = widget.group_grid.itemAt(0).widget()
    card.undo_button.click()
    assert len(widget.locked) == 1
    assert len(widget.rejected) == 2


def test_successful_rethink_keeps_confirmations_and_resets_new_feedback(qtbot, monkeypatch):
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    widget.demo_mode = False
    widget.toggle_lock(0, True)
    monkeypatch.setattr(
        widget.service,
        "solve",
        lambda request, **options: OperationResult(demo_solution(), Usage()),
    )
    widget.start_solve()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert len(widget.locked) == 1
    assert widget.group_grid.count() == 4
    for index in range(4):
        card = widget.group_grid.itemAt(index).widget()
        assert not card.lock_button.isChecked()
        assert not card.reject_button.isChecked()
    assert widget.copy_button.isEnabled()


def test_feedback_buttons_are_adjacent_and_have_visible_exclusive_states(qtbot):
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    card = widget.group_grid.itemAt(0).widget()
    assert card.reject_button.isCheckable()
    assert card.lock_button.objectName() == "FeedbackCorrect"
    assert card.reject_button.objectName() == "FeedbackIncorrect"
    widget.toggle_rejection(0)
    card = widget.group_grid.itemAt(0).widget()
    assert card.reject_button.isChecked()
    assert not card.lock_button.isChecked()


def test_replaced_cards_are_hidden_before_deferred_deletion(qtbot):
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    old_card = widget.group_grid.itemAt(0).widget()
    assert old_card.isVisible()
    widget.toggle_lock(0, True)
    assert not old_card.isVisible()
