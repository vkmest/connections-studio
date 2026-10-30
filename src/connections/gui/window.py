"""Desktop workflow and session state. Puzzle rules remain in the shared models."""

import json
from pathlib import Path

from PySide6.QtCore import QBuffer, QEvent, QIODevice, Qt, QThread, Slot
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from connections.cli import parse_word_text
from connections.config import Settings
from connections.demo import DEMO_WORDS, demo_solution
from connections.gui.settings_dialog import SettingsDialog
from connections.gui.theme import STYLE
from connections.gui.widgets import (
    CapturePreview,
    GridMark,
    GroupCard,
    button,
    label,
)
from connections.gui.worker import Worker
from connections.images import PreparedImage, prepare_image, read_image
from connections.models import Group, Solution, SolveRequest, validate_words
from connections.providers import PROVIDERS
from connections.service import OperationResult, SolverService


class MainWindow(QMainWindow):
    def __init__(self, service: SolverService | None = None):
        super().__init__()
        configuration_error = ""
        if service is None:
            try:
                settings = Settings.from_environment()
            except ValueError:
                # Recovery has no credentials and cannot silently send to a fallback provider.
                settings = Settings()
                configuration_error = (
                    "Could not load configuration. Check CONNECTIONS_PROVIDER and "
                    "CONNECTIONS_MODEL in your environment/.env. Open Settings to choose a "
                    "provider for this session. No credentials were loaded."
                )
            service = SolverService(settings)
        self.service = service
        self.prepared_image: PreparedImage | None = None
        self.solution: Solution | None = None
        self.locked: list[Group] = []
        self.rejected: list[list[str]] = []
        self._awaiting_rethink = False
        self._submitted_locks: set[frozenset[str]] = set()
        self.demo_mode = False
        self.busy = False
        self.session_cost = 0.0
        self.cost_incomplete = False
        self._thread: QThread | None = None
        self._worker: Worker | None = None
        self._operation = ""
        self.setWindowTitle("Connections Studio")
        self.resize(1320, 900)
        self.setMinimumSize(1060, 740)
        self.setStyleSheet(STYLE)
        self.setAcceptDrops(True)
        self._build()
        self.mode.currentIndexChanged.connect(self._refresh)
        self._refresh()
        if configuration_error:
            self._message(configuration_error)
        QApplication.instance().installEventFilter(self)
        QShortcut(QKeySequence.StandardKey.Open, self, activated=self.open_image)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.start_solve)
        QShortcut(QKeySequence.StandardKey.New, self, activated=self.new_puzzle)

    def _build(self):
        root = QWidget()
        root.setObjectName("Root")
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._sidebar())
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.setContentsMargins(32, 22, 32, 18)
        layout.setSpacing(14)
        top = QHBoxLayout()
        top.addWidget(label("YOUR DAILY DOSE OF AHA.", "Eyebrow"))
        top.addStretch()
        self.key_status = label("", "Pill")
        top.addWidget(self.key_status)
        self.settings_button = button("Settings", "Ghost", self.open_settings)
        top.addWidget(self.settings_button)
        layout.addLayout(top)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.message_label = label("", "Message", wrap=True)
        self.message_label.setAccessibleName("Status message")
        self.message_label.hide()
        layout.addWidget(self.message_label)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._workspace())
        self.pages.addWidget(self._results_page())
        self.scroll.setWidget(self.pages)
        layout.addWidget(self.scroll, 1)
        foot = QHBoxLayout()
        foot.addWidget(
            label("Made for curious minds.  ·  Independent of The New York Times.", "Muted")
        )
        foot.addStretch()
        self.cost_label = label("Session API estimate  $0.0000", "Muted")
        foot.addWidget(self.cost_label)
        layout.addLayout(foot)
        outer.addWidget(right, 1)
        self.setCentralWidget(root)

    def _sidebar(self):
        panel = QFrame()
        panel.setObjectName("Sidebar")
        panel.setFixedWidth(206)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 32, 22, 22)
        layout.setSpacing(8)
        layout.addWidget(GridMark(38))
        layout.addSpacing(13)
        layout.addWidget(label("connections", "Brand"))
        layout.addWidget(label("S T U D I O", "BrandSub"))
        layout.addSpacing(36)
        layout.addWidget(label("YOUR WORKSPACE", "Eyebrow"))
        layout.addSpacing(8)
        self.workspace_nav = button("01   The puzzle", "Nav", self.show_workspace)
        self.workspace_nav.setCheckable(True)
        self.workspace_nav.setChecked(True)
        self.results_nav = button("02   Connections", "Nav", self.show_results)
        self.results_nav.setCheckable(True)
        layout.addWidget(self.workspace_nav)
        layout.addWidget(self.results_nav)
        layout.addSpacing(12)
        self.new_button = button("+   New puzzle", "Ghost", self.new_puzzle)
        layout.addWidget(self.new_button)
        layout.addStretch(1)
        note = label("Sixteen words.\nFour little epiphanies.", wrap=True)
        note.setStyleSheet("font-family:Georgia;font-size:21px;color:#777E6E;")
        layout.addWidget(note)
        layout.addSpacing(14)
        self.demo_button = button("Try an example  ↗", "Ghost", self.load_demo)
        layout.addWidget(self.demo_button)
        layout.addWidget(button("How it works", "Ghost", self.show_help))
        layout.addSpacing(18)
        layout.addWidget(label("LOCAL APP   /   v1.0", "Eyebrow"))
        return panel

    def _workspace(self):
        page = QWidget()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 8, 12)
        layout.setSpacing(14)
        layout.addWidget(label("A FRESH PERSPECTIVE", "Eyebrow"))
        layout.addWidget(label("Find the hidden thread.", "Hero"))
        layout.addWidget(
            label(
                "Paste a puzzle. Check the words. Let the connections come into focus.",
                "Subtitle",
                wrap=True,
            )
        )
        layout.addSpacing(6)
        columns = QHBoxLayout()
        columns.setSpacing(20)
        capture = QFrame()
        capture.setObjectName("Card")
        left = QVBoxLayout(capture)
        left.setContentsMargins(24, 24, 24, 24)
        left.setSpacing(14)
        left.addWidget(label("01   /   CAPTURE", "Eyebrow"))
        left.addWidget(label("Start with a screenshot", "CardTitle"))
        self.preview = CapturePreview()
        left.addWidget(self.preview, 1)
        self.paste_button = button("Paste screenshot   Ctrl+V", "Primary", self.paste_clipboard)
        left.addWidget(self.paste_button)
        self.open_button = button("or open an image", "Ghost", self.open_image)
        left.addWidget(self.open_button)
        self.extract_button = button("Read words from image  →", "", self.start_extract)
        left.addWidget(self.extract_button)
        self.image_note = label(
            "Capture just the 4 × 4 grid. Nothing is sent until you click Read words.",
            "Muted",
            wrap=True,
        )
        left.addWidget(self.image_note)
        columns.addWidget(capture, 4)
        board = QFrame()
        board.setObjectName("Card")
        right = QVBoxLayout(board)
        right.setContentsMargins(24, 24, 24, 24)
        right.setSpacing(16)
        heading = QHBoxLayout()
        heading.addWidget(label("02   /   REVIEW", "Eyebrow"))
        heading.addStretch()
        self.word_count = label("0 / 16 words", "Muted")
        heading.addWidget(self.word_count)
        right.addLayout(heading)
        right.addWidget(label("Every word matters.", "CardTitle"))
        right.addWidget(label("Edit any tile, or paste a list of 16 words.", "Subtitle", wrap=True))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.word_inputs = []
        for index in range(16):
            entry = QLineEdit()
            entry.setObjectName("Word")
            entry.setPlaceholderText(f"{index + 1:02d}")
            entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
            entry.setMinimumWidth(50)
            entry.setMinimumHeight(57)
            entry.setMaxLength(80)
            entry.setAccessibleName(f"Word {index + 1}")
            entry.setToolTip(f"Tile {index + 1} · multiword phrases stay together")
            entry.textEdited.connect(self._words_edited)
            grid.addWidget(entry, index // 4, index % 4)
            self.word_inputs.append(entry)
        right.addLayout(grid)
        options = QHBoxLayout()
        options.addWidget(label("SOLVING STYLE", "Eyebrow"))
        options.addStretch()
        self.mode = QComboBox()
        self.mode.addItem("Budget · everyday", "budget")
        self.mode.addItem("Deeper · tricky puzzles", "deeper")
        self.mode.addItem("Extended · more time/tokens", "extended")
        self.mode.setAccessibleName("Solving style")
        self.mode.setToolTip(
            "Budget: 3,500 tokens. Deeper: 6,500. Extended: 16,000 and a five-minute "
            "request timeout. Larger allowances can increase cloud costs."
        )
        options.addWidget(self.mode)
        right.addLayout(options)
        self.solve_button = button("Find connections  →", "Primary", self.start_solve)
        right.addWidget(self.solve_button)
        self.board_note = label("16 unique words unlock your next aha moment.", "Muted", wrap=True)
        right.addWidget(self.board_note)
        columns.addWidget(board, 5)
        layout.addLayout(columns)
        tip = QFrame()
        tip.setObjectName("Tip")
        tip_layout = QHBoxLayout(tip)
        tip_layout.setContentsMargins(20, 16, 20, 16)
        tip_layout.addWidget(label("A LITTLE HEAD START", "Eyebrow"))
        tip_layout.addSpacing(18)
        tip_layout.addWidget(
            label(
                "On Windows, press Win + Shift + S, select the grid, then paste here.",
                "Subtitle",
                wrap=True,
            ),
            1,
        )
        layout.addWidget(tip)
        layout.addStretch()
        return page

    def _results_page(self):
        page = QWidget()
        page.setObjectName("Page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 8, 12)
        layout.setSpacing(14)
        layout.addWidget(label("THE BIG PICTURE", "Eyebrow"))
        layout.addWidget(label("Four ways it all fits.", "Hero"))
        self.results_subtitle = label("", "Subtitle", wrap=True)
        layout.addWidget(self.results_subtitle)
        toolbar = QHBoxLayout()
        toolbar.addWidget(button("←  Edit the words", "Ghost", self.show_workspace))
        toolbar.addStretch()
        self.copy_button = button("Copy answer", "", self.copy_answer)
        self.export_button = button("Export JSON", "", self.export_answer)
        toolbar.addWidget(self.copy_button)
        toolbar.addWidget(self.export_button)
        layout.addLayout(toolbar)
        self.group_grid = QGridLayout()
        self.group_grid.setSpacing(16)
        self.group_grid.setColumnStretch(0, 1)
        self.group_grid.setColumnStretch(1, 1)
        layout.addLayout(self.group_grid)
        bottom = QHBoxLayout()
        self.feedback_note = label("", "Subtitle", wrap=True)
        bottom.addWidget(self.feedback_note, 1)
        self.clear_feedback = button("Clear feedback", "Ghost", self.reset_feedback)
        bottom.addWidget(self.clear_feedback)
        self.retry_button = button("Rethink remaining  →", "Primary", self.start_solve)
        bottom.addWidget(self.retry_button)
        layout.addLayout(bottom)
        layout.addWidget(
            label(
                "Suggestions, not certainties. Confidence is the model's own assessment, "
                "not a measured probability. Colors distinguish groups; "
                "they do not predict the game's difficulty colors.",
                "Muted",
                wrap=True,
            )
        )
        layout.addStretch()
        return page

    def _message(self, text: str):
        self.message_label.setText(text)
        self.message_label.setVisible(bool(text))

    def _refresh(self):
        words = [entry.text() for entry in self.word_inputs]
        count = sum(bool(word.strip()) for word in words)
        self.word_count.setText(f"{count} / 16 words")
        try:
            SolveRequest(words=words)
            valid = True
            note = (
                "Extended: 16,000 tokens · up to five minutes per request. "
                "May increase cloud cost and local memory use."
                if self.mode.currentData() == "extended"
                else "Ready when you are. Each word will be used exactly once."
            )
        except ValueError:
            valid = False
            note = "Use 16 unique words. Check for empty or duplicate tiles."
        self.board_note.setText(
            "Offline example · no API credits needed." if self.demo_mode else note
        )
        self.solve_button.setText(
            "Reveal example groups  →" if self.demo_mode else "Find connections  →"
        )
        self.solve_button.setEnabled(valid and not self.busy)
        self.extract_button.setEnabled(self.prepared_image is not None and not self.busy)
        self.extract_button.setVisible(self.prepared_image is not None)
        for control in (
            self.paste_button,
            self.open_button,
            self.settings_button,
            self.new_button,
            self.demo_button,
            self.mode,
            *self.word_inputs,
        ):
            control.setEnabled(not self.busy)
        self.results_nav.setEnabled(self.solution is not None)
        can_export = self.solution is not None and not self.busy and not self._awaiting_rethink
        self.copy_button.setEnabled(can_export)
        self.export_button.setEnabled(can_export)
        self.retry_button.setEnabled(
            self.solution is not None
            and len(self.locked) < 4
            and not self.busy
            and not self.demo_mode
        )
        self.clear_feedback.setEnabled(not self.busy and bool(self.locked or self.rejected))
        self.key_status.setText(
            "Offline example"
            if self.demo_mode
            else (
                "Ollama · local"
                if self.service.settings.provider == "ollama"
                else PROVIDERS[self.service.settings.provider].name
                + (" · key ready" if self.service.settings.api_key else " · key needed")
            )
        )
        destination = PROVIDERS[self.service.settings.provider].name
        note = (
            "Runs on your computer. No cloud API charge."
            if self.service.settings.provider == "ollama"
            else f"Sends data to {destination}. Uses that provider's API credits."
        )
        self.extract_button.setToolTip(note)
        self.solve_button.setToolTip(note)
        self.retry_button.setToolTip(note)
        suffix = " + unpriced usage" if self.cost_incomplete else ""
        self.cost_label.setText(f"Session API estimate  ${self.session_cost:.4f}{suffix}")
        self.cost_label.setToolTip(
            "Known usage only. Check the selected provider for actual billing."
        )
        self.feedback_note.setText(
            f"{len(self.locked)} of 4 confirmed  ·  {len(self.rejected)} rejected sets"
        )

    def _invalidate(self):
        self.solution = None
        self.locked = []
        self.rejected = []
        self._awaiting_rethink = False
        self._submitted_locks.clear()
        self.demo_mode = False
        self._clear_cards()

    def _words_edited(self):
        self._invalidate()
        self._message("")
        self._refresh()

    def set_words(self, words: list[str]):
        self._invalidate()
        for index, entry in enumerate(self.word_inputs):
            entry.setText(words[index] if index < len(words) else "")
        self._refresh()

    def set_image(self, data: bytes):
        if self.busy:
            return
        prepared = prepare_image(data)
        self.set_words([])
        self.prepared_image = prepared
        self.preview.set_image(prepared.data)
        self.image_note.setText(
            f"{prepared.width} × {prepared.height} px · ready to read. "
            "Read words sends this preview to the selected provider."
        )
        self._message(
            "Screenshot ready. Click Read words to extract the grid, then review each tile."
        )
        self.show_workspace()
        self._refresh()

    def paste_clipboard(self):
        if self.busy:
            return
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        try:
            if not image.isNull():
                if image.width() * image.height() > 25_000_000:
                    raise ValueError("Image is too large. Capture just the puzzle grid.")
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buffer, "PNG")
                self.set_image(bytes(buffer.data()))
            elif clipboard.text().strip():
                words = parse_word_text(clipboard.text())
                if len(words) != 16:
                    raise ValueError(
                        f"Found {len(words)} entries. Paste 16 words separated by "
                        "newlines, commas or tabs. Keep phrases together."
                    )
                self.set_words(validate_words(words, 16))
                self.prepared_image = None
                self.preview.set_image(None)
                self.show_workspace()
                self._message("Words pasted. Check the tiles, then find connections.")
                self._refresh()
            else:
                self._message("Your clipboard has no image or words. Capture the grid first.")
        except ValueError as error:
            self._message(str(error))

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.KeyPress
            and event.matches(QKeySequence.StandardKey.Paste)
            and self.isActiveWindow()
            and QApplication.activeModalWidget() is None
        ):
            clipboard = QApplication.clipboard()
            if not clipboard.image().isNull() or len(parse_word_text(clipboard.text())) > 1:
                self.paste_clipboard()
                return True
        return super().eventFilter(watched, event)

    def open_image(self):
        if self.busy:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open a puzzle screenshot", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if filename:
            self._open_path(filename)

    def _open_path(self, filename: str):
        try:
            image = read_image(Path(filename))
            self.set_image(image.data)
        except (OSError, ValueError) as error:
            self._message(str(error))

    def dragEnterEvent(self, event):
        if not self.busy and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.busy:
            self._open_path(event.mimeData().urls()[0].toLocalFile())

    def load_demo(self):
        if self.busy:
            return
        self.set_words(DEMO_WORDS)
        self.prepared_image = None
        self.preview.set_image(None)
        self.demo_mode = True
        self.image_note.setText("An original practice puzzle. Explore the interface for free.")
        self.show_workspace()
        self._message("Example loaded. Reveal its groups to try the workflow without an API key.")
        self._refresh()

    def new_puzzle(self):
        if self.busy:
            return
        if any(entry.text() for entry in self.word_inputs) or self.prepared_image:
            answer = QMessageBox.question(
                self,
                "Start a new puzzle?",
                "Clear this puzzle and its feedback?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.set_words([])
        self.prepared_image = None
        self.preview.set_image(None)
        self.image_note.setText(
            "Capture just the 4 × 4 grid. Nothing is sent until you click Read words."
        )
        self.show_workspace()
        self._message("")
        self._refresh()

    def start_extract(self):
        if self.busy or self.prepared_image is None:
            return
        self._run("extract", lambda: self.service.extract(self.prepared_image))

    def start_solve(self):
        if self.busy:
            return
        try:
            request = SolveRequest(
                words=[entry.text() for entry in self.word_inputs],
                locked=self.locked,
                rejected=self.rejected,
                mode=self.mode.currentData(),
            )
        except ValueError:
            self._message("Check the grid: you need exactly 16 unique, nonempty words.")
            return
        if self.demo_mode:
            self.solution = demo_solution()
            self._render_results()
            self.show_results()
            self._message("Offline example · these groups are predefined, with zero API cost.")
            return
        is_rethink = self.solution is not None
        if is_rethink:
            self._awaiting_rethink = True
            self._submitted_locks = {frozenset(group.words) for group in self.locked}
            self._render_results()
        self._run(
            "solve",
            (lambda: self.service.solve(request, fresh=True))
            if is_rethink
            else (lambda: self.service.solve(request)),
        )

    def _run(self, operation: str, callback):
        self.busy = True
        self._operation = operation
        self.progress.show()
        self._message(
            "Reading the grid… This can take a moment."
            if operation == "extract"
            else "Looking for connections… Checking meanings and wordplay."
        )
        self._refresh()
        self._set_cards_enabled(False)
        self._thread = QThread(self)
        self._worker = Worker(callback)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.succeeded.connect(self._succeeded)
        self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _add_usage(self, usage):
        if usage is None or usage.estimated_cost_usd is None:
            self.cost_incomplete = True
        else:
            self.session_cost += usage.estimated_cost_usd

    @Slot(object)
    def _succeeded(self, result: OperationResult):
        self._add_usage(result.usage)
        if self._operation == "extract":
            self.set_words(result.value.words)
            warning = result.value.warning
            self._message(warning or "Words read. Check spelling in all 16 tiles before solving.")
            self.word_inputs[0].setFocus()
        else:
            self._awaiting_rethink = False
            self.solution = result.value
            self._render_results()
            self.show_results()
            self._message(
                "Reused this session's saved answer · no new API charge."
                if result.cached
                else "Connections found. Try a group in the game, then mark it correct here."
            )

    @Slot(object)
    def _failed(self, error):
        self._add_usage(getattr(error, "usage", None))
        self._message(
            "No new answer was accepted. Confirmed groups and rejected sets are still saved. "
            + str(error)
            if self._awaiting_rethink
            else str(error)
        )
        if self._awaiting_rethink:
            self._render_results()

    @Slot()
    def _thread_finished(self):
        self.busy = False
        self._worker = None
        self._thread = None
        self.progress.hide()
        self._refresh()
        self._set_cards_enabled(True)

    def _clear_cards(self):
        while self.group_grid.count():
            item = self.group_grid.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def _render_results(self):
        self._clear_cards()
        if self.solution:
            position = 0
            for index, group in enumerate(self.solution.groups):
                locked = any(set(group.words) == set(item.words) for item in self.locked)
                if self._awaiting_rethink and not locked:
                    continue
                rejected = any(set(group.words) == set(item) for item in self.rejected)
                card = GroupCard(
                    group,
                    index,
                    locked,
                    rejected,
                    submitted=frozenset(group.words) in self._submitted_locks,
                )
                card.lock_changed.connect(self.toggle_lock)
                card.reject_changed.connect(self.toggle_rejection)
                self.group_grid.addWidget(card, position // 2, position % 2)
                position += 1
            if self._awaiting_rethink:
                placeholder = label(
                    "Previous unconfirmed suggestions removed.\n"
                    "New groups will appear here after a valid response.",
                    "Message",
                    wrap=True,
                )
                self.group_grid.addWidget(placeholder, (position + 1) // 2, 0, 1, 2)
            self.results_subtitle.setText(
                "Previous suggestions cleared · confirmed groups kept · feedback saved."
                if self._awaiting_rethink
                else "16 words, each used once. Confirm the hits. Rethink the near misses."
            )
        self._refresh()
        self._set_cards_enabled(not self.busy)

    def _set_cards_enabled(self, enabled: bool):
        for index in range(self.group_grid.count()):
            self.group_grid.itemAt(index).widget().setEnabled(enabled)

    def toggle_lock(self, index: int, checked: bool):
        if self.busy or self.solution is None:
            return
        group = self.solution.groups[index]
        self._submitted_locks.discard(frozenset(group.words))
        self.locked = [item for item in self.locked if set(item.words) != set(group.words)]
        if checked:
            self.locked.append(group.model_copy(deep=True))
        self._render_results()
        if len(self.locked) == 4:
            self._message("All four groups confirmed. A satisfying little click.")

    def toggle_rejection(self, index: int):
        if self.busy or self.solution is None:
            return
        words = self.solution.groups[index].words
        if any(set(words) == set(item) for item in self.rejected):
            self.rejected = [item for item in self.rejected if set(item) != set(words)]
        elif len(self.rejected) < 32:
            self.rejected.append(list(words))
        else:
            self._message("32 rejected sets reached. Clear feedback to start a fresh search.")
        self._render_results()

    def reset_feedback(self):
        if self.busy:
            return
        self.locked = []
        self.rejected = []
        self._submitted_locks.clear()
        # Do not resurrect rejected cards after a failed rethink.
        self._render_results()
        self._message("Feedback cleared. Your current suggestions are still here.")

    def show_workspace(self):
        self.pages.setCurrentIndex(0)
        self.workspace_nav.setChecked(True)
        self.results_nav.setChecked(False)
        self.scroll.verticalScrollBar().setValue(0)

    def show_results(self):
        if self.solution is None:
            return
        self.pages.setCurrentIndex(1)
        self.workspace_nav.setChecked(False)
        self.results_nav.setChecked(True)
        self.scroll.verticalScrollBar().setValue(0)

    def open_settings(self):
        if self.busy:
            return
        dialog = SettingsDialog(self.service.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.service.close()
            self.service = SolverService(dialog.settings())
            self._message(
                dialog.preference_warning
                or "Provider settings updated. Keys are session-only unless you chose "
                "OS credential storage. No keys were written to the project."
            )
            self._refresh()

    def copy_answer(self):
        if self.solution and not self._awaiting_rethink and not self.busy:
            text = "\n\n".join(
                f"{group.title}\n{', '.join(group.words)}\n{group.explanation}"
                for group in self.solution.groups
            )
            QApplication.clipboard().setText(text)
            self._message("Answer copied to the clipboard.")

    def export_answer(self):
        if self.solution is None or self._awaiting_rethink or self.busy:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export suggestions", "connections.json", "JSON (*.json)"
        )
        if filename:
            try:
                payload = {
                    "solution": self.solution.model_dump(),
                    "locked": [group.model_dump() for group in self.locked],
                    "rejected": self.rejected,
                    "demo": self.demo_mode,
                }
                Path(filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")
                self._message("Suggestions exported.")
            except OSError as error:
                self._message("Could not save the file: " + str(error))

    def show_help(self):
        QMessageBox.information(
            self,
            "A small guide to big connections",
            "1. Open an unsolved 4 × 4 Connections grid.\n"
            "2. Capture the grid (Windows: Win+Shift+S; Mac: Ctrl+Cmd+Shift+4).\n"
            "3. Paste here with Ctrl+V / Cmd+V. Click Read words (uses API credits).\n"
            "4. Correct any tile, then click Find connections (uses API credits).\n"
            "5. Try a suggestion in the game. Mark correct groups; reject wrong sets.\n"
            "6. Rethink remaining keeps your confirmed groups.\n\n"
            "You can also type or paste 16 comma/newline-separated entries.\n"
            "Try an example to explore without an API key.\n\n"
            "Images and words stay in memory. Only explicit Read/Find/Rethink actions contact "
            "the selected provider. Ollama runs locally without a key.\n"
            "Settings can save keys in your OS credential store. Hosted providers' "
            "data retention policies apply to cloud requests.",
        )

    def closeEvent(self, event: QCloseEvent):
        if self.busy:
            self._message(
                "A request is still running. Please wait for it to finish before closing."
            )
            event.ignore()
            return
        QApplication.instance().removeEventFilter(self)
        self.service.close()
        event.accept()
