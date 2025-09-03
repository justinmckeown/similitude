# tests/cli/test_cli_flags_smoke.py
from pathlib import Path
from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()


def test_scan_with_enable_and_verbose(tmp_path: Path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "a.txt").write_text("x")
    db = tmp_path / "sim.db"
    res = runner.invoke(
        app,
        [
            "scan",
            "--path",
            str(root),
            "--db",
            str(db),
            "--enable",
            "phash",
            "--verbose",
        ],
    )
    assert res.exit_code == 0, res.output


def test_report_default(tmp_path: Path):
    db = tmp_path / "sim.db"
    # minimal scan to create db
    root = tmp_path / "data"
    root.mkdir()
    (root / "a.txt").write_text("x")
    runner.invoke(app, ["scan", "--path", str(root), "--db", str(db)])
    # exercise report command path
    res = runner.invoke(app, ["report", "--db", str(db), "--fmt", "json"])
    assert res.exit_code == 0, res.output
