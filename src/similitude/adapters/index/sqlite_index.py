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

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Iterator, cast

DDL = """
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    device TEXT,
    inode_or_fileid TEXT,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    ctime_ns INTEGER,
    birthtime_ns INTEGER,
    owner_id TEXT,
    owner_name TEXT,
    seen_at INTEGER NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_files_device_inode
  ON files(device, inode_or_fileid)
  WHERE device IS NOT NULL AND inode_or_fileid IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_mtime_size ON files(mtime_ns, size);

CREATE TABLE IF NOT EXISTS hashes (
    file_id INTEGER PRIMARY KEY,
    pre_hash TEXT,
    strong_hash TEXT,
    phash TEXT,
    ssdeep TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hashes_strong ON hashes(strong_hash);
CREATE INDEX IF NOT EXISTS idx_hashes_pre    ON hashes(pre_hash);

CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class SQLiteIndex:
    """
    Thin, explicit SQLite adapter with minimal, meaningful error handling.

    - Avoids broad try/except: let sqlite3 errors bubble up.
    - Uses one-shot `conn.execute(...)` calls so cursors are short-lived.
    - Implements context manager support (`with SQLiteIndex(...) as idx:`).
    - Provides `__del__` as a best effort to reduce ResourceWarnings in tests.
    - Stores device/inode as TEXT to avoid overflow on Windows.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # --- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        if getattr(self, "_conn", None) is not None:
            self._conn.close()
            self._conn = None  # type: ignore[assignment]

    def __enter__(self) -> SQLiteIndex:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            if getattr(self, "_conn", None) is not None:
                self._conn.close()
        except Exception:
            pass

    # --- public API ---------------------------------------------------------

    def upsert_file(self, file_meta: dict) -> int:
        # Required fields
        try:
            path = str(file_meta["path"])
            size = int(file_meta["size"])
            mtime_ns = int(file_meta["mtime_ns"])
        except Exception as e:
            raise ValueError(f"upsert_file requires path/size/mtime_ns: {e}") from e

        seen_at = int(file_meta.get("seen_at") or time.time())

        device = file_meta.get("device")
        inode = file_meta.get("inode_or_fileid")
        device = None if device in (None, "", 0) else str(device)
        inode = None if inode in (None, "", 0) else str(inode)

        ctime_ns = file_meta.get("ctime_ns")
        birthtime_ns = file_meta.get("birthtime_ns")
        owner_id = file_meta.get("owner_id")
        owner_name = file_meta.get("owner_name")

        ctime_ns = int(ctime_ns) if ctime_ns is not None else None
        birthtime_ns = int(birthtime_ns) if birthtime_ns is not None else None

        # Strong identity
        if device and inode:
            row = self._conn.execute(
                "SELECT id FROM files WHERE device=? AND inode_or_fileid=?",
                (device, inode),
            ).fetchone()
            if row:
                file_id = cast(int, row["id"])
                self._conn.execute(
                    """
                    UPDATE files
                    SET path=?, size=?, mtime_ns=?, ctime_ns=?, birthtime_ns=?,
                        owner_id=?, owner_name=?, seen_at=?
                    WHERE id=?
                    """,
                    (
                        path,
                        size,
                        mtime_ns,
                        ctime_ns,
                        birthtime_ns,
                        owner_id,
                        owner_name,
                        seen_at,
                        file_id,
                    ),
                )
                return file_id

        # Fallback identity
        row = self._conn.execute(
            "SELECT id FROM files WHERE path=? AND size=? AND mtime_ns=?",
            (path, size, mtime_ns),
        ).fetchone()
        if row:
            file_id = cast(int, row["id"])
            self._conn.execute(
                """
                UPDATE files
                SET device=?, inode_or_fileid=?, ctime_ns=?, birthtime_ns=?,
                    owner_id=?, owner_name=?, seen_at=?
                WHERE id=?
                """,
                (
                    device,
                    inode,
                    ctime_ns,
                    birthtime_ns,
                    owner_id,
                    owner_name,
                    seen_at,
                    file_id,
                ),
            )
            return file_id

        # Insert new
        cur = self._conn.execute(
            """
            INSERT INTO files (device, inode_or_fileid, path, size, mtime_ns,
                               ctime_ns, birthtime_ns, owner_id, owner_name, seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device,
                inode,
                path,
                size,
                mtime_ns,
                ctime_ns,
                birthtime_ns,
                owner_id,
                owner_name,
                seen_at,
            ),
        )
        return cast(int, cur.lastrowid)

    def upsert_hashes(self, file_id: int, hashes: dict) -> None:
        pre_hash = hashes.get("pre_hash")
        strong_hash = hashes.get("strong_hash")
        phash = hashes.get("phash")
        ssdeep = hashes.get("ssdeep")

        row = self._conn.execute(
            "SELECT file_id FROM hashes WHERE file_id=?",
            (file_id,),
        ).fetchone()
        if row:
            self._conn.execute(
                """
                UPDATE hashes
                SET pre_hash=?, strong_hash=?, phash=?, ssdeep=?
                WHERE file_id=?
                """,
                (pre_hash, strong_hash, phash, ssdeep, file_id),
            )
        else:
            self._conn.execute(
                """
                INSERT INTO hashes (file_id, pre_hash, strong_hash, phash, ssdeep)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, pre_hash, strong_hash, phash, ssdeep),
            )

    def find_duplicates(self) -> Iterable[list[dict[str, Any]]]:
        cur = self._conn.execute(
            """
            SELECT strong_hash
            FROM hashes
            WHERE strong_hash IS NOT NULL AND strong_hash != ''
            GROUP BY strong_hash
            HAVING COUNT(*) > 1
            """
        )
        for row in cur.fetchall():
            yield list(self._rows_for_strong_hash(cast(str, row["strong_hash"])))

    # --- helpers ------------------------------------------------------------

    def _init_schema(self) -> None:
        self._conn.executescript(DDL)

    def _rows_for_strong_hash(self, strong_hash: str) -> Iterator[dict[str, Any]]:
        cur = self._conn.execute(
            """
            SELECT f.*, h.pre_hash, h.strong_hash, h.phash, h.ssdeep
            FROM hashes h
            JOIN files f ON f.id = h.file_id
            WHERE h.strong_hash = ?
            ORDER BY f.path ASC
            """,
            (strong_hash,),
        )
        for r in cur.fetchall():
            yield {k: r[k] for k in r.keys()}
