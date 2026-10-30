"""Provider selection and explicit, OS-backed credential persistence."""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
)

from connections.config import Settings
from connections.credentials import CredentialError, CredentialStore
from connections.gui.widgets import button, label
from connections.preferences import save_preferences
from connections.providers import PROVIDERS


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._selected_settings = settings
        self.preference_warning = ""
        self._forget_pending = False
        self.setWindowTitle("Providers & keys · Connections Studio")
        self.setMinimumWidth(550)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(13)
        layout.addWidget(label("Your models. Your keys.", "CardTitle"))
        layout.addWidget(
            label(
                "Choose a hosted provider or run entirely on your computer.", "Subtitle", wrap=True
            )
        )
        layout.addWidget(label("PROVIDER", "Eyebrow"))
        self.provider_input = QComboBox()
        self.provider_input.setAccessibleName("Model provider")
        for key, provider in PROVIDERS.items():
            self.provider_input.addItem(provider.name, key)
        self.provider_input.setCurrentIndex(self.provider_input.findData(settings.provider))
        layout.addWidget(self.provider_input)
        self.destination = label("", "Muted", wrap=True)
        layout.addWidget(self.destination)
        layout.addWidget(label("API KEY", "Eyebrow"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setAccessibleName("Selected provider API key")
        layout.addWidget(self.key_input)
        self.remember = QCheckBox("Remember key in the operating system credential store")
        layout.addWidget(self.remember)
        self.forget_button = button("Forget this provider's saved key", "Ghost", self.forget_key)
        layout.addWidget(self.forget_button)
        layout.addWidget(
            label(
                "Unchecked: use this key for this session; existing saved keys are unchanged.\n"
                "Windows uses Credential Manager. The app never writes keys to project files.\n"
                "Switching provider discards unsaved key edits.",
                "Muted",
                wrap=True,
            )
        )
        layout.addWidget(label("MODEL", "Eyebrow"))
        self.model_input = QLineEdit()
        self.model_input.setMaxLength(200)
        self.model_input.setAccessibleName("Model name")
        layout.addWidget(self.model_input)
        self.model_note = label("", "Muted", wrap=True)
        layout.addWidget(self.model_note)
        self.status = label("", "Message", wrap=True)
        self.status.hide()
        layout.addWidget(self.status)
        links = QHBoxLayout()
        self.setup_button = button("Provider setup ↗", "Ghost", self.open_setup)
        links.addWidget(self.setup_button)
        links.addStretch()
        layout.addLayout(links)
        controls = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        controls.accepted.connect(self.accept)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)
        self._display(settings)
        self.provider_input.currentIndexChanged.connect(self._provider_changed)

    def _display(self, settings: Settings):
        provider = PROVIDERS[settings.provider]
        local = settings.provider == "ollama"
        self._forget_pending = False
        self.remember.setChecked(False)
        self.remember.setEnabled(not local)
        self.key_input.clear()
        self.key_input.setEnabled(not local)
        self.key_input.setText(settings.api_key if not local else "")
        self.key_input.setPlaceholderText("No key needed" if local else "Paste this provider's key")
        self.forget_button.setEnabled(not local)
        self.model_input.setText(settings.model)
        self.destination.setText("Destination: " + provider.base_url)
        notes = {
            "openai": "Default: gpt-5.4-mini. Budget: low; Deeper/Extended: medium reasoning.\n"
            "Reference rates: $0.75 input / $4.50 output per million tokens.",
            "kimi": "Default: kimi-k3.1-pro. Hosted API, billed by Moonshot.\n"
            "Budget uses low reasoning; Deeper uses high. Kimi K2.5 API is retired.",
            "deepseek": "Default: deepseek-flash. Hosted API, billed by DeepSeek.\n"
            "Budget disables thinking; Deeper enables high reasoning.",
            "ollama": "Install Ollama, then run: ollama pull qwen3-vl:4b\n"
            "No per-request API bill. Needs local compute and model storage.\n"
            "Only local GGUF models are accepted. Disable Ollama cloud features too.",
        }
        self.model_note.setText(notes[settings.provider])
        self.status.hide()

    def _provider_changed(self):
        provider = self.provider_input.currentData()
        try:
            self._display(Settings.from_environment(provider=provider))
        except ValueError:
            self._display(Settings(provider=provider))
            self.status.setText("Invalid environment model setting. Enter a supported model below.")
            self.status.show()

    def forget_key(self):
        self.key_input.clear()
        self.remember.setChecked(False)
        self._forget_pending = True
        self.status.setText(
            "Click Save to remove this provider's stored key. "
            "Environment/.env keys must be removed separately."
        )
        self.status.show()

    def open_setup(self):
        QDesktopServices.openUrl(QUrl(PROVIDERS[self.provider_input.currentData()].setup_url))

    def accept(self):
        try:
            settings = Settings(
                provider=self.provider_input.currentData(),
                model=self.model_input.text(),
                api_key=self.key_input.text().strip(),
            )
            store = CredentialStore()
            if self.remember.isChecked():
                store.save(settings.provider, settings.api_key)
            elif self._forget_pending:
                store.forget(settings.provider)
        except (CredentialError, ValueError) as error:
            self.status.setText(str(error))
            self.status.show()
            return
        try:
            save_preferences(settings)
        except OSError:
            # Credential changes already succeeded; don't present a cancellable failed Save.
            self.preference_warning = (
                "Settings applied for this session; any requested key save/removal succeeded. "
                "Could not save provider/model preferences. Check your user folder permissions."
            )
        self._selected_settings = settings
        self.key_input.clear()
        super().accept()

    def settings(self) -> Settings:
        return self._selected_settings

    def reject(self):
        self.key_input.clear()
        super().reject()
