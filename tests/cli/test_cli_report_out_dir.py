# tests/cli/test_cli_report_out_dir.py
from pathlib import Path
from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()


def test_report_writes_into_output_directory(tmp_path: Path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "a.txt").write_text("x")
    db = tmp_path / "sim.db"

    # create some data
    assert (
        runner.invoke(app, ["scan", "--path", str(root), "--db", str(db)]).exit_code
        == 0
    )

    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    r = runner.invoke(
        app, ["report", "--db", str(db), "--fmt", "json", "--out", str(out_dir)]
    )
    assert r.exit_code == 0, r.output

    target = out_dir / "duplicates.json"
    assert target.exists() and target.stat().st_size > 0
