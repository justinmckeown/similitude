# tests/unit/test_report_service_formats.py
import json
from pathlib import Path
from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.services.report_service import ReportService


def _seed_two_dupes_one_unique(idx: SQLiteIndex):
    # Two duplicate files -> same strong hash
    f1 = idx.upsert_file({"path": "a.txt", "size": 1, "mtime_ns": 1})
    idx.upsert_hashes(f1, {"strong_hash": "dup"})
    f2 = idx.upsert_file({"path": "b.txt", "size": 2, "mtime_ns": 2})
    idx.upsert_hashes(f2, {"strong_hash": "dup"})
    # One unique file
    f3 = idx.upsert_file({"path": "c.txt", "size": 3, "mtime_ns": 3})
    idx.upsert_hashes(f3, {"strong_hash": "unique"})


def test_report_json_with_duplicates(tmp_path: Path):
    db = tmp_path / "r1.db"
    idx = SQLiteIndex(db)
    _seed_two_dupes_one_unique(idx)

    out = tmp_path / "dupes.json"
    report = ReportService(idx)

    # explicit JSON format
    path = report.write_duplicates(out, fmt="json")
    assert path == out
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1  # exactly one cluster
    paths = {rec["path"] for rec in data[0]}
    assert paths == {"a.txt", "b.txt"}


def test_report_json_with_no_duplicates(tmp_path: Path):
    db = tmp_path / "r2.db"
    idx = SQLiteIndex(db)

    # Only unique files
    f1 = idx.upsert_file({"path": "x.txt", "size": 10, "mtime_ns": 1})
    idx.upsert_hashes(f1, {"strong_hash": "X"})
    f2 = idx.upsert_file({"path": "y.txt", "size": 11, "mtime_ns": 2})
    idx.upsert_hashes(f2, {"strong_hash": "Y"})

    out = tmp_path / "empty.json"
    report = ReportService(idx)

    path = report.write_duplicates(out, fmt="json")
    assert path == out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload == []  # no clusters
