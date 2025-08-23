from pathlib import Path
from similitude.adapters.index.sqlite_index import SQLiteIndex


def test_upsert_file_strong_identity_update(tmp_path: Path):
    db = tmp_path / "t.db"
    with SQLiteIndex(db) as idx:
        a1 = {
            "path": "a.txt",
            "size": 100,
            "mtime_ns": 1,
            "device": "DEV1",
            "inode_or_fileid": "INODE1",
        }
        id1 = idx.upsert_file(a1)

        # same strong identity, changed metadata → UPDATE same row
        a2 = {
            "path": "a_renamed.txt",
            "size": 200,
            "mtime_ns": 2,
            "device": "DEV1",
            "inode_or_fileid": "INODE1",
        }
        id2 = idx.upsert_file(a2)
        assert id2 == id1  # updated in place


def test_upsert_file_fallback_identity_update(tmp_path: Path):
    db = tmp_path / "t2.db"
    with SQLiteIndex(db) as idx:
        # No device/inode → fallback identity (path+size+mtime_ns)
        b1 = {"path": "b.txt", "size": 42, "mtime_ns": 7}
        id1 = idx.upsert_file(b1)

        # Same fallback identity triplet → UPDATE same row (attach device/inode now)
        b2 = {
            "path": "b.txt",
            "size": 42,
            "mtime_ns": 7,
            "device": "DEVX",
            "inode_or_fileid": "INODEX",
        }
        id2 = idx.upsert_file(b2)
        assert id2 == id1


def test_upsert_hashes_insert_then_update(tmp_path: Path):
    db = tmp_path / "t3.db"
    with SQLiteIndex(db) as idx:
        fid = idx.upsert_file({"path": "h.txt", "size": 1, "mtime_ns": 1})
        idx.upsert_hashes(
            fid, {"pre_hash": "p1", "strong_hash": "s1", "phash": None, "ssdeep": None}
        )
        # update same row (change strong hash)
        idx.upsert_hashes(
            fid, {"pre_hash": "p2", "strong_hash": "s2", "phash": None, "ssdeep": None}
        )

        # No duplicates expected with a single file id
        assert list(idx.find_duplicates()) == []


def test_find_duplicates_and_rows_for_strong_hash(tmp_path: Path):
    db = tmp_path / "t4.db"
    with SQLiteIndex(db) as idx:
        # Two files share same strong hash → one cluster
        f1 = idx.upsert_file({"path": "c1.txt", "size": 10, "mtime_ns": 1})
        idx.upsert_hashes(f1, {"strong_hash": "same"})
        f2 = idx.upsert_file({"path": "c2.txt", "size": 11, "mtime_ns": 2})
        idx.upsert_hashes(f2, {"strong_hash": "same"})

        # A third file with different hash → not part of duplicates
        f3 = idx.upsert_file({"path": "c3.txt", "size": 12, "mtime_ns": 3})
        idx.upsert_hashes(f3, {"strong_hash": "different"})

        clusters = list(idx.find_duplicates())
        assert len(clusters) == 1
        paths = {rec["path"] for rec in clusters[0]}
        assert paths == {"c1.txt", "c2.txt"}


def test_find_duplicates_empty(tmp_path: Path):
    db = tmp_path / "t5.db"
    with SQLiteIndex(db) as idx:
        assert list(idx.find_duplicates()) == []
