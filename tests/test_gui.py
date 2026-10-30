import io

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from connections.config import Settings
from connections.demo import DEMO_WORDS, demo_solution
from connections.gui.widgets import GroupCard
from connections.gui.window import MainWindow
from connections.models import SolveRequest, Usage
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
    assert widget.capture_prompt.isVisible()
    assert widget.capture_prompt.read_button.isDefault()


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
    assert widget.random_fallback
    widget.solution.validate_for(SolveRequest(words=DEMO_WORDS))


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
    assert not widget.busy_dialog.isVisible()


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
    assert "Random test arrangement" in widget.message_label.text()
    assert "Random" in widget.results_subtitle.text()
    widget.solution.validate_for(captured[0])
    assert len(widget.locked) == 2 and len(widget.rejected) == 2
    assert widget.copy_button.isEnabled()
    assert widget.export_button.isEnabled()
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


def test_extended_style_is_explicit_and_warns_about_cost(qtbot):
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)
    widget.mode.setCurrentIndex(widget.mode.findData("extended"))
    assert widget.mode.currentData() == "extended"
    assert "16,000" in widget.board_note.text()
    assert "cost" in widget.board_note.text().lower()


def test_sidebar_can_be_closed_and_reopened_without_losing_puzzle(qtbot):
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)
    assert widget.mode.currentData() == "extended"
    widget.sidebar_close.click()
    assert widget.sidebar.isHidden()
    widget.sidebar_toggle.click()
    assert not widget.sidebar.isHidden()
    assert widget.word_inputs[0].text() == DEMO_WORDS[0]


def test_theme_switch_is_saved_and_survives_provider_preferences(qtbot):
    from connections.preferences import save_preferences

    widget = window(qtbot)
    widget.theme_toggle.click()
    assert widget.theme == "dark"
    save_preferences(Settings(api_key="never-save-this"))
    other = window(qtbot)
    assert other.theme == "dark"
    other.theme_toggle.click()
    assert other.theme == "light"


def test_capture_popup_requires_explicit_read_and_busy_dialog_is_centered(qtbot, monkeypatch):
    from threading import Event

    release = Event()
    widget = window(qtbot)
    calls = []

    def extract(image):
        calls.append(image)
        release.wait(timeout=3)
        raise ServiceError("Test read failure")

    monkeypatch.setattr(widget.service, "extract", extract)
    image = QImage(300, 300, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    QApplication.clipboard().setImage(image)
    widget.paste_clipboard()
    assert not calls and not widget.busy
    widget.capture_prompt.read_button.click()
    try:
        assert not widget.capture_prompt.isVisible()
        assert widget.busy_dialog.isVisible()
        center = widget.mapToGlobal(widget.rect().center())
        assert (widget.busy_dialog.geometry().center() - center).manhattanLength() <= 3
        assert not widget.message_label.isVisible()
        widget.busy_dialog.reject()
        assert not widget.busy_dialog.isVisible()
        assert not widget.busy
    finally:
        release.set()
        qtbot.waitUntil(lambda: not widget._jobs, timeout=5000)
    assert len(calls) == 1
    assert not widget.busy_dialog.isVisible()
    assert "Stopped waiting" in widget.message_label.text()
    assert "Test read failure" not in widget.message_label.text()


def test_completed_puzzle_has_new_puzzle_action_that_returns_home(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    def unexpected_question(*args):
        raise AssertionError("Completed puzzle should reset directly")

    monkeypatch.setattr(QMessageBox, "question", unexpected_question)
    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    for index in range(4):
        widget.toggle_lock(index, True)
    assert widget.retry_button.text() == "New puzzle  →"
    assert widget.retry_button.isEnabled()
    assert "No API request" in widget.retry_button.toolTip()
    assert widget.new_button.isHidden()
    widget.retry_button.click()
    assert widget.pages.currentIndex() == 0
    assert widget.solution is None and not widget.locked and not widget.attempt_history
    assert all(not field.text() for field in widget.word_inputs)
    assert widget.prepared_image is None
    assert not widget.new_button.isHidden()


def test_rethink_includes_history_and_remembers_refused_attempts(qtbot, monkeypatch):

    widget = window(qtbot)
    widget.load_demo()
    widget.start_solve()
    assert widget.clear_feedback.isEnabled()
    widget.demo_mode = False
    old = demo_solution()
    changed = demo_solution()
    changed.groups[2].words[0], changed.groups[3].words[0] = (
        changed.groups[3].words[0],
        changed.groups[2].words[0],
    )
    captured = []

    def fail(request, **options):
        captured.append(request)
        raise ServiceError("Rejected candidate", attempt=changed)

    monkeypatch.setattr(widget.service, "solve", fail)
    widget.start_solve()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert captured[0].previous_attempts == [old]
    fallback = widget.solution.model_copy(deep=True)
    widget.start_solve()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert captured[1].previous_attempts == [old, changed, fallback]
    widget.clear_feedback.click()
    assert widget.attempt_history == []
    assert not widget.clear_feedback.isEnabled()
    widget.set_words(DEMO_WORDS)
    assert widget.attempt_history == []


def test_stop_waiting_is_immediate_and_late_response_cannot_overwrite_fallback(qtbot, monkeypatch):
    from threading import Event

    release = Event()
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)

    def slow(request):
        release.wait(timeout=3)
        return OperationResult(demo_solution(), Usage())

    monkeypatch.setattr(widget.service, "solve", slow)
    widget.start_solve()
    try:
        widget.busy_dialog.cancel_button.click()
        assert not widget.busy and not widget.busy_dialog.isVisible()
        assert widget.random_fallback
        fallback = widget.solution.model_dump()
        assert "Random" in widget.results_subtitle.text()
        assert widget.solve_button.isEnabled()
    finally:
        release.set()
        qtbot.waitUntil(lambda: not widget._jobs, timeout=5000)
    assert widget.solution.model_dump() == fallback


def test_cancelled_operation_cannot_clear_busy_state_of_a_new_request(qtbot, monkeypatch):
    from threading import Event

    first = Event()
    second = Event()
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)

    def old(request):
        first.wait(timeout=3)
        return OperationResult(demo_solution(), Usage())

    def current(request, **options):
        second.wait(timeout=3)
        return OperationResult(demo_solution(), Usage())

    monkeypatch.setattr(widget.service, "solve", old)
    widget.start_solve()
    widget.cancel_operation()
    monkeypatch.setattr(widget.service, "solve", current)
    widget.start_solve()
    try:
        first.set()
        qtbot.waitUntil(lambda: len(widget._jobs) == 1, timeout=5000)
        assert widget.busy and widget.busy_dialog.isVisible()
    finally:
        first.set()
        second.set()
        qtbot.waitUntil(lambda: not widget._jobs, timeout=5000)
    assert not widget.busy and not widget.random_fallback


def test_window_can_close_after_stopping_without_waiting_for_provider(qtbot, monkeypatch):
    from threading import Event

    release = Event()
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)

    def slow(request):
        release.wait(timeout=3)
        return OperationResult(demo_solution(), Usage())

    monkeypatch.setattr(widget.service, "solve", slow)
    widget.start_solve()
    widget.cancel_operation()
    try:
        assert widget.close()
        assert not widget.isVisible()
    finally:
        release.set()
        qtbot.waitUntil(lambda: not widget._jobs, timeout=5000)


def test_failed_extraction_never_randomly_fills_unread_words(qtbot, monkeypatch):
    widget = window(qtbot)
    stream = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(stream, "PNG")
    widget.set_image(stream.getvalue())

    def fail(image):
        raise ServiceError("Image could not be read")

    monkeypatch.setattr(widget.service, "extract", fail)
    widget.start_extract()
    qtbot.waitUntil(lambda: not widget.busy, timeout=5000)
    assert widget.solution is None and not widget.random_fallback
    assert all(not field.text() for field in widget.word_inputs)
    assert "Image could not be read" in widget.message_label.text()


def test_cancel_after_worker_finishes_before_queued_signals_closes_retired_client_once(
    qtbot, monkeypatch
):
    widget = window(qtbot)
    widget.set_words(DEMO_WORDS)
    retired = widget.service
    closed = []
    monkeypatch.setattr(retired, "close", lambda: closed.append(True))
    monkeypatch.setattr(retired, "solve", lambda request: OperationResult(demo_solution(), Usage()))
    widget.start_solve()
    widget._thread.join(timeout=2)
    assert widget.busy
    widget.cancel_operation()
    qtbot.waitUntil(lambda: not widget._jobs, timeout=5000)
    assert closed == [True]


def test_cancel_before_worker_starts_makes_no_provider_call(qtbot):
    from connections.gui.worker import Worker

    calls = []
    service = SolverService(Settings())
    worker = Worker(lambda: calls.append(True), service)
    worker.cancel()
    worker.thread.start()
    worker.thread.join(timeout=2)
    assert not calls
