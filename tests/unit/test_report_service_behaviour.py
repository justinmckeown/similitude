import json
import pytest
from pathlib import Path

from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.services.report_service import ReportService


def _seed_two_dupes_one_unique(index: SQLiteIndex) -> None:
    # Two files share the same strong hash -> one duplicate cluster
    f1 = index.upsert_file({"path": "a.txt", "size": 1, "mtime_ns": 1})
    index.upsert_hashes(f1, {"strong_hash": "dup"})
    f2 = index.upsert_file({"path": "b.txt", "size": 2, "mtime_ns": 2})
    index.upsert_hashes(f2, {"strong_hash": "dup"})
    # One unique file (different strong hash)
    f3 = index.upsert_file({"path": "c.txt", "size": 3, "mtime_ns": 3})
    index.upsert_hashes(f3, {"strong_hash": "unique"})


def test_report_defaults_to_json(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r1.db") as idx:
        _seed_two_dupes_one_unique(idx)
        out = tmp_path / "dupes.json"
        rep = ReportService(idx)

        # No fmt provided -> defaults to JSON
        written = rep.write_duplicates(out)
        assert written == out
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1
        assert {rec["path"] for rec in data[0]} == {"a.txt", "b.txt"}


def test_report_json_when_empty(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r2.db") as idx:
        out = tmp_path / "empty.json"
        rep = ReportService(idx)
        written = rep.write_duplicates(out, fmt="json")
        assert written == out
        assert json.loads(out.read_text(encoding="utf-8")) == []


def test_report_path_can_be_directory(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r3.db") as idx:
        _seed_two_dupes_one_unique(idx)
        rep = ReportService(idx)

        # Simulate CLI logic: if user passes a directory, we would resolve to dir/duplicates.json
        out_dir = tmp_path / "reports"
        out_dir.mkdir()
        target = out_dir / "duplicates.json"

        written = rep.write_duplicates(target, fmt="json")
        assert written == target
        data = json.loads(target.read_text(encoding="utf-8"))
        assert len(data) == 1


def test_report_rejects_unsupported_format(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r4.db") as idx:
        rep = ReportService(idx)
        p = tmp_path / "dupes.something"
        with pytest.raises(ValueError) as excinfo:
            rep.write_duplicates(p, fmt="bogus")
        assert "unsupported" in str(excinfo.value).lower()
