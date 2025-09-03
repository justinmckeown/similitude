# tests/cli/test_cli_enable_validation.py
from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()


def test_scan_unknown_feature_fails_cleanly():
    r = runner.invoke(
        app, ["scan", "--path", ".", "--db", "sim.db", "--enable", "notafeature"]
    )
    assert r.exit_code != 0
    assert "Unknown feature(s)" in r.output
