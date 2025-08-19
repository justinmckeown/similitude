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

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Iterator, cast

from ...ports.index import IndexPort

logger = logging.getLogger(__name__)

DDL = """
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

-- Prefer strong identity when present
CREATE UNIQUE INDEX IF NOT EXISTS ux_files_device_inode
  ON files(device, inode_or_fileid)
  WHERE device IS NOT NULL AND inode_or_fileid IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_mtime_size ON files(mtime_ns, size);

CREATE TABLE IF NOT EXISTS hashes (
    file_id INTEGER PRIMARY KEY,  -- 1:1 for MVP
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


class SQLiteIndex(IndexPort):
    """
    SQLite implementation of IndexPort.

    Notes:
      * Creates schema automatically.
      * WAL mode enabled; NORMAL synchronous for speed with reasonable durability.
      * `upsert_file` uses (device,inode_or_fileid) when present, else (path,size,mtime_ns).
      * `device` and `inode_or_fileid` are stored as TEXT to accommodate wide identifiers (e.g., Windows).
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, isolation_level=None)  # autocommit
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # -------------------------
    # lifecycle
    # -------------------------

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            # best-effort close
            pass

    # -------------------------
    # IndexPort API
    # -------------------------

    def upsert_file(self, file_meta: dict) -> int:
        """
        Insert or update a file record; return its ID.

        Required (MVP): path, size, mtime_ns
        Optional: device, inode_or_fileid, ctime_ns, birthtime_ns, owner_id, owner_name, seen_at
        """
        cur = self._conn.cursor()

        # Normalize inputs
        seen_at = int(file_meta.get("seen_at") or time.time())

        # Device / inode can be very large on Windows (e.g., 128-bit).
        # Store them as TEXT to avoid SQLite INTEGER overflow.
        raw_device = file_meta.get("device")
        raw_inode = file_meta.get("inode_or_fileid")
        device = None if raw_device in (None, "", 0) else str(raw_device)
        inode = None if raw_inode in (None, "", 0) else str(raw_inode)

        path = str(file_meta["path"])
        size = int(file_meta["size"])

        # Timestamps as 64-bit-compatible ints (or None)
        mtime_ns = int(file_meta["mtime_ns"])
        ctime_ns = file_meta.get("ctime_ns")
        birthtime_ns = file_meta.get("birthtime_ns")
        owner_id = file_meta.get("owner_id")
        owner_name = file_meta.get("owner_name")

        ctime_ns = int(ctime_ns) if ctime_ns is not None else None
        birthtime_ns = int(birthtime_ns) if birthtime_ns is not None else None

        try:
            # 1) Strong identity: device + inode
            if device and inode:
                try:
                    cur.execute(
                        "SELECT id FROM files WHERE device = ? AND inode_or_fileid = ?",
                        (device, inode),
                    )
                except sqlite3.Error as e:
                    logger.error(
                        "SQLiteIndex.upsert_file: SELECT strong identity failed",
                        extra={"path": path, "device": device, "inode": inode, "err": str(e)},
                    )
                    raise

                row = cur.fetchone()
                if row:
                    file_id = cast(int, row["id"])
                    try:
                        cur.execute(
                            """
                            UPDATE files
                            SET path = ?, size = ?, mtime_ns = ?, ctime_ns = ?, birthtime_ns = ?,
                                owner_id = ?, owner_name = ?, seen_at = ?
                            WHERE id = ?
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
                    except sqlite3.Error as e:
                        logger.error(
                            "SQLiteIndex.upsert_file: UPDATE by strong identity failed",
                            extra={"id": file_id, "path": path, "err": str(e)},
                        )
                        raise
                    finally:
                        try:
                            cur.close()
                        except Exception:
                            pass
                    return file_id

            # 2) Fallback identity: path + size + mtime_ns
            try:
                cur.execute(
                    "SELECT id FROM files WHERE path = ? AND size = ? AND mtime_ns = ?",
                    (path, size, mtime_ns),
                )
            except sqlite3.Error as e:
                logger.error(
                    "SQLiteIndex.upsert_file: SELECT fallback identity failed",
                    extra={"path": path, "size": size, "mtime_ns": mtime_ns, "err": str(e)},
                )
                raise

            row = cur.fetchone()
            if row:
                file_id = cast(int, row["id"])
                try:
                    cur.execute(
                        """
                        UPDATE files
                        SET device = ?, inode_or_fileid = ?, ctime_ns = ?, birthtime_ns = ?,
                            owner_id = ?, owner_name = ?, seen_at = ?
                        WHERE id = ?
                        """,
                        (device, inode, ctime_ns, birthtime_ns, owner_id, owner_name, seen_at, file_id),
                    )
                except sqlite3.Error as e:
                    logger.error(
                        "SQLiteIndex.upsert_file: UPDATE by fallback identity failed",
                        extra={"id": file_id, "path": path, "err": str(e)},
                    )
                    raise
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
                return file_id

            # 3) Insert new row
            try:
                cur.execute(
                    """
                    INSERT INTO files (device, inode_or_fileid, path, size, mtime_ns,
                                       ctime_ns, birthtime_ns, owner_id, owner_name, seen_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (device, inode, path, size, mtime_ns, ctime_ns, birthtime_ns, owner_id, owner_name, seen_at),
                )
            except sqlite3.IntegrityError as e:
                logger.error(
                    "SQLiteIndex.upsert_file: INSERT integrity error",
                    extra={"path": path, "device": device, "inode": inode, "err": str(e)},
                )
                raise
            except sqlite3.Error as e:
                logger.error(
                    "SQLiteIndex.upsert_file: INSERT failed",
                    extra={"path": path, "err": str(e)},
                )
                raise

            file_id = cast(int, cur.lastrowid)
            return file_id

        finally:
            try:
                cur.close()
            except Exception:
                pass

    def upsert_hashes(self, file_id: int, hashes: dict) -> None:
        pre_hash = hashes.get("pre_hash")
        strong_hash = hashes.get("strong_hash")
        phash = hashes.get("phash")
        ssdeep = hashes.get("ssdeep")

        cur = self._conn.cursor()
        try:
            try:
                cur.execute("SELECT file_id FROM hashes WHERE file_id = ?", (file_id,))
            except sqlite3.Error as e:
                logger.error(
                    "SQLiteIndex.upsert_hashes: SELECT failed",
                    extra={"file_id": file_id, "err": str(e)},
                )
                raise

            row = cur.fetchone()
            if row:
                try:
                    cur.execute(
                        """
                        UPDATE hashes
                        SET pre_hash = ?, strong_hash = ?, phash = ?, ssdeep = ?
                        WHERE file_id = ?
                        """,
                        (pre_hash, strong_hash, phash, ssdeep, file_id),
                    )
                except sqlite3.Error as e:
                    logger.error(
                        "SQLiteIndex.upsert_hashes: UPDATE failed",
                        extra={"file_id": file_id, "err": str(e)},
                    )
                    raise
            else:
                try:
                    cur.execute(
                        """
                        INSERT INTO hashes (file_id, pre_hash, strong_hash, phash, ssdeep)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (file_id, pre_hash, strong_hash, phash, ssdeep),
                    )
                except sqlite3.IntegrityError as e:
                    logger.error(
                        "SQLiteIndex.upsert_hashes: INSERT integrity error",
                        extra={"file_id": file_id, "err": str(e)},
                    )
                    raise
                except sqlite3.Error as e:
                    logger.error(
                        "SQLiteIndex.upsert_hashes: INSERT failed",
                        extra={"file_id": file_id, "err": str(e)},
                    )
                    raise
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def find_duplicates(self) -> Iterable[list[dict[str, Any]]]:
        """
        Yield clusters (lists) of file dicts for files sharing the same strong_hash.
        Only clusters with size > 1 are returned.
        """
        cur = self._conn.cursor()
        try:
            try:
                cur.execute(
                    """
                    SELECT strong_hash
                    FROM hashes
                    WHERE strong_hash IS NOT NULL AND strong_hash != ''
                    GROUP BY strong_hash
                    HAVING COUNT(*) > 1
                    """
                )
            except sqlite3.Error as e:
                logger.error("SQLiteIndex.find_duplicates: SELECT groups failed", extra={"err": str(e)})
                raise

            for row in cur.fetchall():
                strong = row["strong_hash"]
                yield list(self._rows_for_strong_hash(cast(str, strong)))
        finally:
            try:
                cur.close()
            except Exception:
                pass

    # -------------------------
    # Helpers
    # -------------------------

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        try:
            cur.executescript(DDL)
        except sqlite3.Error as e:
            logger.error("SQLiteIndex._init_schema: DDL failed", extra={"err": str(e)})
            raise
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def _rows_for_strong_hash(self, strong_hash: str) -> Iterator[dict[str, Any]]:
        cur = self._conn.cursor()
        try:
            try:
                cur.execute(
                    """
                    SELECT f.*, h.pre_hash, h.strong_hash, h.phash, h.ssdeep
                    FROM hashes h
                    JOIN files f ON f.id = h.file_id
                    WHERE h.strong_hash = ?
                    ORDER BY f.path ASC
                    """,
                    (strong_hash,),
                )
            except sqlite3.Error as e:
                logger.error(
                    "SQLiteIndex._rows_for_strong_hash: SELECT failed",
                    extra={"strong_hash": strong_hash, "err": str(e)},
                )
                raise

            for r in cur.fetchall():
                yield {k: r[k] for k in r.keys()}
        finally:
            try:
                cur.close()
            except Exception:
                pass
