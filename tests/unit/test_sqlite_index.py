import time
from pathlib import Path
from similitude.adapters.index.sqlite_index import SQLiteIndex


def test_sqlite_index_upsert_and_duplicates(tmp_path: Path):
    db = tmp_path / "similitude.db"
    now = int(time.time())
    with SQLiteIndex(db) as idx:
        # Insert two different files with the same strong hash
        f1 = {
            "path": str(tmp_path / "a.txt"),
            "size": 3,
            "mtime_ns": now * 1_000_000_000,
            "device": "dev1",
            "inode_or_fileid": "1",
            "seen_at": now,
        }
        f2 = {
            "path": str(tmp_path / "b.txt"),
            "size": 3,
            "mtime_ns": now * 1_000_000_000,
            "device": "dev1",
            "inode_or_fileid": "2",
            "seen_at": now,
        }

        id1 = idx.upsert_file(f1)
        id2 = idx.upsert_file(f2)

        idx.upsert_hashes(id1, {"pre_hash": "pX", "strong_hash": "SAME"})
        idx.upsert_hashes(id2, {"pre_hash": "pY", "strong_hash": "SAME"})

        clusters = list(idx.find_duplicates())
        assert len(clusters) == 1
        assert {rec["path"] for rec in clusters[0]} == {f1["path"], f2["path"]}
