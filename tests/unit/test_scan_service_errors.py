from pathlib import Path
from typing import Iterator
from similitude.services.scan_service import ScanService
from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.ports.filesystem import FilesystemPort
from similitude.ports.hasher import HasherPort


class FSWithBadStat(FilesystemPort):
    def walk(self, root: Path) -> Iterator[Path]:
        yield root / "ok.txt"
        yield root / "bad.txt"

    def stat(self, path: Path) -> dict:
        if path.name == "bad.txt":
            # simulate unreadable file
            raise OSError("permission denied")
        st = path.stat()
        return {
            "path": str(path),
            "size": st.st_size,
            "mtime_ns": int(getattr(st, "st_mtime_ns", st.st_mtime * 1e9)),
        }

    def open_bytes(self, path: Path, chunk_size: int = 65536) -> Iterator[bytes]:
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
            if chunk:
                yield chunk


class FlakyHasher(HasherPort):
    def __init__(self, fail_on: str):
        self.fail_on = fail_on

    @property
    def name(self) -> str:
        return "flaky"

    def hash_stream(self, fh) -> str:
        # This hasher will raise to hit the except paths in ScanService
        # Callers open the file, we just simulate a failure on read
        _ = fh.read(1)
        if self.fail_on == "pre":
            raise ValueError("pre-hash failed")
        if self.fail_on == "strong":
            raise ValueError("strong-hash failed")
        return "ok"


def test_scan_covers_stat_and_hash_exceptions(tmp_path: Path):
    (tmp_path / "ok.txt").write_text("hello")
    (tmp_path / "bad.txt").write_text("secret")

    db = tmp_path / "t.db"
    idx = SQLiteIndex(db)
    fs = FSWithBadStat()

    pre = FlakyHasher(fail_on="pre")
    strong = FlakyHasher(fail_on="strong")

    svc = ScanService(fs, pre, strong, idx)
    processed = svc.scan(tmp_path)
    # ok.txt processed; bad.txt skipped due to stat error
    assert processed == 1
