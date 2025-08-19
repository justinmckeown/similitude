import json
from pathlib import Path
from typing import Iterator

from similitude.services import ScanService, ReportService
from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.ports.filesystem import FilesystemPort
from similitude.ports.hasher import HasherPort

# We reuse the lightweight hashers from the CLI wiring to keep the test realistic.
from similitude.cli.app import PreHasher, SHA256Hasher
import inspect

print("USING ScanService from:", ScanService.__module__)
print("FILE:", inspect.getsourcefile(ScanService))


class LocalTestFS(FilesystemPort):
    """Concrete FS adapter for tests using the real local filesystem via pathlib."""

    def walk(self, root: Path) -> Iterator[Path]:
        root = Path(root)
        if root.is_file():
            print(f"YIELD File: {root}")
            yield root
            return
        for p in root.rglob("*"):
            if p.is_file():
                print(f"YIELD file: {p}")
                yield p

    def stat(self, path: Path) -> dict:
        st = path.stat()
        return {
            "path": str(path),
            "size": st.st_size,
            "mtime_ns": getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)),
            "ctime_ns": getattr(st, "st_ctime_ns", int(st.st_ctime * 1e9)),
            "device": getattr(st, "st_dev", 0),
            "inode_or_fileid": getattr(st, "st_ino", 0),
        }

    def open_bytes(self, path: Path, chunk_size: int = 65536) -> Iterator[bytes]:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk


def write_file(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def test_scan_and_report_duplicates(tmp_path: Path):
    # Arrange: create three files: a.txt and b.txt are duplicates; c.txt is different
    root = tmp_path / "data"
    a = root / "a.txt"
    b = root / "nested" / "b.txt"
    c = root / "c.txt"

    write_file(a, b"hello world\n")
    write_file(b, b"hello world\n")  # exact duplicate of a
    write_file(c, b"something else\n")

    db = tmp_path / "similitude.db"
    index = SQLiteIndex(db)

    fs = LocalTestFS()
    pre: HasherPort = PreHasher(first_n=1024)
    strong: HasherPort = SHA256Hasher()

    scan = ScanService(fs, pre, strong, index)
    report = ReportService(index)

    # Act: scan the directory and produce a JSON report
    processed = scan.scan(root)
    out = tmp_path / "duplicates.json"
    report.write_duplicates(out, fmt="json")

    # Assert: all files processed; one duplicate cluster with the two identical files
    assert processed == 3
    assert out.exists()

    clusters = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(clusters, list)
    # Expect exactly one cluster (a & b), c is unique
    assert len(clusters) == 1
    paths = {rec["path"] for rec in clusters[0]}
    assert paths == {str(a), str(b)}

    index.close()
