import json

from termivance.cli import main


def test_policy_check_example_disabled(capsys):
    rc = main(["policy-check", "config/retirement_policy.example.json", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mutation_enabled"] is False
    assert payload["safe_read_only"] is True


def test_policy_check_missing_fails(capsys):
    assert main(["policy-check", "does/not/exist.json"]) == 2
    assert "policy-error" in capsys.readouterr().err


def test_doctor_ok(capsys):
    assert main(["doctor"]) == 0
    assert "ok=True" in capsys.readouterr().out
