# tests/unit/test_scan_ignore.py
from pathlib import Path
from similitude.services.scan_service import ScanService
from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.ports.filesystem import FilesystemPort
from typing import Iterator


# Realistic local FS adapter (same contract as integration test)
class LocalTestFS(FilesystemPort):
    def walk(self, root: Path) -> Iterator[Path]:
        root = Path(root)
        if root.is_file():
            yield root
            return
        for p in root.rglob("*"):
            if p.is_file():
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


def test_scan_respects_ignore_patterns(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create actual files on disk inside the data dir (not alongside the DB)
    (data_dir / "ignore_me.txt").write_text("ignored\n")
    (data_dir / "include_me.txt").write_text("included\n")

    db = tmp_path / "test.db"  # DB sits OUTSIDE the scan root (data_dir)
    index = SQLiteIndex(db)
    fs = LocalTestFS()

    from similitude.cli.app import PreHasher, SHA256Hasher

    pre = PreHasher(first_n=1024)
    strong = SHA256Hasher()

    # Use a basename-friendly pattern so it works across OSes
    scan = ScanService(fs, pre, strong, index, ignore_patterns=["*ignore_me.txt"])
    processed = scan.scan(data_dir)

    # Only "include_me.txt" should be processed
    assert processed == 1
