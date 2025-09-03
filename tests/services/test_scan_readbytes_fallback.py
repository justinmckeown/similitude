# tests/services/test_scan_readbytes_fallback.py
from pathlib import Path
from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()


def test_scan_fallback_to_streaming_when_read_bytes_fails(tmp_path: Path, monkeypatch):
    # Arrange: small file (so scan tries the in-memory path first)
    root = tmp_path / "data"
    root.mkdir()
    f = root / "a.txt"
    f.write_text("hello")

    db = tmp_path / "sim.db"

    # Monkeypatch Path.read_bytes to raise for THIS specific file to push code into the stream fallback
    orig_read_bytes = Path.read_bytes

    def flaky_read_bytes(self: Path):
        if self == f:
            raise OSError("simulated read failure")
        return orig_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", flaky_read_bytes, raising=True)

    r = runner.invoke(app, ["scan", "--path", str(root), "--db", str(db)])
    assert (
        r.exit_code == 0
    ), r.output  # scan should still succeed via streaming fallback
