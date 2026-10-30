import json

from connections.cli import main


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
