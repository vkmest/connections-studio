import json

from connections.cli import main
from connections.credentials import CredentialStore


def test_demo_json_runs_without_key_or_network(capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["solve", "--demo", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["solution"]["groups"]) == 4
    assert payload["usage"]["estimated_cost_usd"] == 0


def test_bad_word_count_exits_cleanly(capsys):
    assert main(["solve", "--words", "ONE,TWO"]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert "16" in output.err


def test_missing_file_exits_cleanly(capsys):
    assert main(["solve", "--image", "does-not-exist.png"]) == 1
    assert "Error" in capsys.readouterr().err


def test_provider_and_model_overrides_stay_together(monkeypatch):
    from connections import cli
    from connections.demo import demo_solution
    from connections.models import Usage
    from connections.service import OperationResult

    selected = []

    class FakeService:
        def __init__(self, settings):
            selected.append(settings)

        def solve(self, request):
            return OperationResult(demo_solution(), Usage())

        def close(self):
            pass

    monkeypatch.setattr(cli, "SolverService", FakeService)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-go-to-ollama")
    words = ",".join(word for group in demo_solution().groups for word in group.words)
    assert main(["solve", "--words", words, "--provider", "ollama", "--model", "qwen3-vl:8b"]) == 0
    assert selected[0].provider == "ollama"
    assert selected[0].model == "qwen3-vl:8b"
    assert selected[0].api_key == ""


def test_auth_hidden_prompt_and_provider_specific_removal(monkeypatch, capsys):
    from connections import cli

    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "secret-cli-test")
    assert main(["auth", "set", "--provider", "kimi"]) == 0
    store = CredentialStore()
    assert store.get("kimi") == "secret-cli-test"
    assert store.get("openai") == ""
    assert main(["auth", "status", "--provider", "kimi"]) == 0
    assert "secret-cli-test" not in capsys.readouterr().out
    assert main(["auth", "forget", "--provider", "kimi"]) == 0
    assert store.get("kimi") == ""


def test_auth_refuses_a_piped_key(capsys):
    assert main(["auth", "set", "--provider", "openai"]) == 1
    assert "interactive terminal" in capsys.readouterr().err
