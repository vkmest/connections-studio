import pytest
from PySide6.QtWidgets import QDialog, QLineEdit

from connections.config import Settings
from connections.credentials import CredentialStore
from connections.gui.settings_dialog import SettingsDialog
from connections.preferences import load_preferences


def test_provider_switch_does_not_reuse_key(qtbot, monkeypatch):
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    dialog = SettingsDialog(Settings(api_key="openai-private"))
    qtbot.addWidget(dialog)
    assert dialog.key_input.echoMode() == QLineEdit.EchoMode.Password
    dialog.provider_input.setCurrentIndex(dialog.provider_input.findData("kimi"))
    assert dialog.key_input.text() == ""
    assert dialog.model_input.text() == "kimi-k3.1-pro"
    dialog.provider_input.setCurrentIndex(dialog.provider_input.findData("ollama"))
    assert not dialog.key_input.isEnabled()
    assert dialog.key_input.text() == ""


def test_remember_key_uses_vault_not_preferences(qtbot):
    dialog = SettingsDialog(Settings())
    qtbot.addWidget(dialog)
    dialog.key_input.setText("private-test-value")
    dialog.remember.setChecked(True)
    dialog.accept()
    assert CredentialStore().get("openai") == "private-test-value"
    assert load_preferences() == {"provider": "openai", "model": "gpt-5.4-mini"}
    assert dialog.settings().api_key == "private-test-value"


def test_cancel_never_saves_new_key(qtbot):
    dialog = SettingsDialog(Settings())
    qtbot.addWidget(dialog)
    dialog.key_input.setText("never-save")
    dialog.remember.setChecked(True)
    dialog.reject()
    assert CredentialStore().get("openai") == ""


def test_forget_commits_on_save_only(qtbot):
    store = CredentialStore()
    store.save("openai", "old-key")
    dialog = SettingsDialog(Settings(api_key="old-key"))
    qtbot.addWidget(dialog)
    dialog.forget_key()
    assert store.get("openai") == "old-key"
    dialog.accept()
    assert store.get("openai") == ""


@pytest.mark.parametrize("forget", [False, True])
def test_preferences_failure_does_not_hide_completed_key_change(qtbot, monkeypatch, forget):
    from connections.gui import settings_dialog

    def unavailable(settings):
        raise OSError("private path detail")

    monkeypatch.setattr(settings_dialog, "save_preferences", unavailable)
    store = CredentialStore()
    store.save("openai", "old-key")
    dialog = SettingsDialog(Settings(api_key="old-key"))
    qtbot.addWidget(dialog)
    if forget:
        dialog.forget_key()
    else:
        dialog.key_input.setText("new-key")
        dialog.remember.setChecked(True)
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert store.get("openai") == ("" if forget else "new-key")
    assert dialog.settings().api_key == ("" if forget else "new-key")
    assert "could not save" in dialog.preference_warning.lower()
    assert "private path" not in dialog.preference_warning
