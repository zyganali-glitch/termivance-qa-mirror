from termivance import __version__
from termivance.cli import main


def test_status_is_truthful(capsys):
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "source=local_snapshot_not_live" in out
    assert "retirement=" in out


def test_status_json(capsys):
    assert main(["status", "--json"]) == 0
    out = capsys.readouterr().out
    assert '"source": "local_snapshot_not_live"' in out
    assert '"product": "Termivance"' in out


def test_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__
