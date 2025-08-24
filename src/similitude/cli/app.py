# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
from typing import Iterator, Optional, BinaryIO, List


import hashlib
import typer

from ..ports.filesystem import FilesystemPort
from ..ports.hasher import HasherPort
from ..ports.similarity import SimilarityPort

from ..services import ScanService, ReportService
from ..adapters.index.sqlite_index import SQLiteIndex
from ..adapters.similarity.image_phash import ImagePHash
from ..adapters.similarity.ssdeep_adapter import SsdeepAdapter

from ..logging_config import setup_logging

setup_logging()

app = typer.Typer(help="Similitude CLI - File intelligence and duplicate detection")


# ------------------------------
# Placeholder Adapters (stubs)
# ------------------------------


class LocalFS(FilesystemPort):
    """Minimal local filesystem adapter suitable for early wiring."""

    def walk(self, root: Path) -> Iterator[Path]:
        root = Path(root)
        if root.is_file():
            yield root
            return
        for dirpath, _dirnames, filenames in os.walk(root):
            d = Path(dirpath)
            for name in filenames:
                yield d / name

    def stat(self, path: Path) -> dict:
        st = path.stat()
        # NOTE: st_ctime is "creation" on Windows/APFS, "inode change" on Linux.
        # We capture raw values; later we will normalize in an adapter.
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


class PreHasher(HasherPort):
    """
    Fast pre-hash: BLAKE2b of the first N bytes, salted with file size.
    Not cryptographic for equality, but good for bucketing candidates.
    """

    def __init__(self, first_n: int = 1 << 20):  # default 1 MiB
        self._first_n = int(first_n)

    @property
    def name(self) -> str:
        return f"blake2b_first{self._first_n}"

    def hash_stream(self, stream: BinaryIO) -> str:
        h = hashlib.blake2b(digest_size=16)
        remaining = self._first_n
        # Consume up to first_n bytes
        while remaining > 0:
            chunk = stream.read(min(65536, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
        # Best effort: if stream has a tell/seek, get size by seeking to end and back
        try:
            pos = stream.tell()
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(pos, os.SEEK_SET)
        except Exception:
            size = 0
        h.update(size.to_bytes(8, "little", signed=False))
        return h.hexdigest()


class SHA256Hasher(HasherPort):
    """Cryptographic strong hash (full-file SHA-256)."""

    @property
    def name(self) -> str:
        return "sha256"

    def hash_stream(self, stream: BinaryIO) -> str:
        h = hashlib.sha256()
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()


# ------------------------------
# CLI Commands
# ------------------------------


def _wire(
    db_path: str, enable: Optional[List[str]] = None
) -> tuple[ScanService, ReportService]:
    """
    Minimal composition root:
      LocalFS + PreHasher + SHA256Hasher + DummySQLiteIndex
    """
    fs = LocalFS()
    pre = PreHasher(first_n=1 << 20)  # 1 MiB
    strong = SHA256Hasher()
    index = SQLiteIndex(db_path)

    features = {s.strip().lower() for s in (enable or []) if s.strip()}
    adapters: List[SimilarityPort] = []
    enable_phash = "phash" in features
    enable_ssdeep = "ssdeep" in features

    if enable_phash:
        adapters.append(ImagePHash())
    if enable_ssdeep:
        adapters.append(SsdeepAdapter())

    scan = ScanService(
        fs,
        pre,
        strong,
        index,
        similarity_adapters=adapters,
        enable_phash=enable_phash,
        enable_ssdeep=enable_ssdeep,
    )

    report = ReportService(index)
    return scan, report


@app.command()
def scan(
    path: str,
    db: str = "similitude.db",
    enable: Optional[str] = typer.Option(
        None, "--enable", help="Comma-separated features: phash,ssdeep"
    ),
):
    """
    Scan a directory, compute pre-hash + strong-hash, and update the index.
    """
    enable_list = enable.split(",") if enable else None
    scan_service, _ = _wire(db, enable=enable_list)
    count = scan_service.scan(Path(path))
    typer.echo(f"Scanned {path}; processed {count} files; index: {db}")


@app.command()
def report(
    db: Path = typer.Option(
        "similitude.db",
        "--db",
        help="Path to the SQLite index file.",
        exists=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    fmt: str = typer.Option(
        "json",
        "--fmt",
        help="Output format.",
        case_sensitive=False,
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "--output",
        help="Write report to this path. If a directory is provided, the file will be named 'duplicates.<fmt>' inside it. "
        "If omitted entirely, defaults to './duplicates.<fmt>'.",
        resolve_path=True,
    ),
):
    """
    Generate a duplicate report from the index.
    """
    # index = SQLiteIndex(db)
    with SQLiteIndex(db) as index:
        report = ReportService(index)

        # Determine target path:
        # - no --out  -> ./duplicates.<fmt>
        # - --out DIR -> DIR/duplicates.<fmt>
        # - --out FILE -> FILE
        if out is None:
            target = Path(f"duplicates.{fmt}")
        else:
            out = Path(out)
            if out.exists() and out.is_dir():
                target = out / f"duplicates.{fmt}"
            else:
                # If the path doesn't exist yet, we treat it as a file path.
                # (ReportService will create parent dirs.)
                target = out

        written = report.write_duplicates(target, fmt=fmt)
        typer.echo(f"Wrote {fmt} report to {written}")
