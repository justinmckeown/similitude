from pathlib import Path
from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()


def test_cli_scan_and_report_roundtrip(tmp_path: Path):
    # Arrange
    root = tmp_path / "data"
    (root / "nested").mkdir(parents=True)
    a = root / "a.txt"
    b = root / "nested" / "b.txt"
    c = root / "c.txt"

    root.mkdir(parents=True)
    (root / "nested").mkdir(parents=True)

    a.write_text("hello world\n")
    b.write_text("hello world\n")
    c.write_text("something else\n")

    db = tmp_path / "similitude.db"
    out = tmp_path / "duplicates.json"

    # Act
    result_scan = runner.invoke(app, ["scan", "--path", str(root), "--db", str(db)])
    assert result_scan.exit_code == 0, result_scan.output

    result_report = runner.invoke(
        app, ["report", "--db", str(db), "--fmt", "json", "--out", str(out)]
    )
    assert result_report.exit_code == 0, result_report.output

    # Assert
    assert out.exists(), "Expected duplicates report to be written"
    assert out.stat().st_size > 0, "Report should not be empty"
    # clusters = json.loads(out.read_text())
    # assert len(clusters) == 1
    # paths = {rec["path"] for rec in clusters[0]}
    # assert str(a) in paths and str(b) in paths
