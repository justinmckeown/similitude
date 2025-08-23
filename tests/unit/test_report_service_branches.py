import json
from pathlib import Path
from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.services.report_service import ReportService


def _seed_dupes(idx: SQLiteIndex):
    a = idx.upsert_file({"path": "a.txt", "size": 1, "mtime_ns": 1})
    b = idx.upsert_file({"path": "b.txt", "size": 1, "mtime_ns": 2})
    idx.upsert_hashes(a, {"strong_hash": "dup"})
    idx.upsert_hashes(b, {"strong_hash": "dup"})


def test_report_defaults_to_json(tmp_path: Path):
    db = tmp_path / "r.db"
    idx = SQLiteIndex(db)
    _seed_dupes(idx)

    out = tmp_path / "dupes.json"
    report = ReportService(idx)
    # Omit fmt on purpose (cover default)
    path = report.write_duplicates(out)
    assert path == out
    data = json.loads(out.read_text("utf-8"))
    assert len(data) == 1
    paths = {rec["path"] for rec in data[0]}
    assert paths == {"a.txt", "b.txt"}


def test_report_json_no_duplicates(tmp_path: Path):
    db = tmp_path / "r2.db"
    idx = SQLiteIndex(db)

    out = tmp_path / "empty.json"
    report = ReportService(idx)
    path = report.write_duplicates(out, fmt="json")
    assert path == out
    assert json.loads(out.read_text("utf-8")) == []
