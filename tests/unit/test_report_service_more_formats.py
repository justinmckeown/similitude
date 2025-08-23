import csv
import json
from pathlib import Path

from similitude.adapters.index.sqlite_index import SQLiteIndex
from similitude.services.report_service import ReportService


def _seed(idx: SQLiteIndex):
    """Two dupes (same strong hash) + one unique."""
    a = idx.upsert_file({"path": "a.txt", "size": 1, "mtime_ns": 1})
    b = idx.upsert_file({"path": "b.txt", "size": 2, "mtime_ns": 2})
    idx.upsert_hashes(a, {"strong_hash": "dup"})
    idx.upsert_hashes(b, {"strong_hash": "dup"})
    c = idx.upsert_file({"path": "c.txt", "size": 3, "mtime_ns": 3})
    idx.upsert_hashes(c, {"strong_hash": "unique"})


def test_report_ndjson(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r_nd.db") as idx:
        _seed(idx)

        out = tmp_path / "dupes.ndjson"
        report = ReportService(idx)

        written = report.write_duplicates(out, fmt="ndjson")
        assert written == out

        # Don't use .strip(); it can hide newline semantics.
        text = out.read_text(encoding="utf-8")
        # Non-empty file: expect exactly one non-empty line (one cluster)
        lines = [ln for ln in text.splitlines() if ln]
        assert len(lines) == 1

        arr = json.loads(lines[0])
        paths = {rec["path"] for rec in arr}
        assert paths == {"a.txt", "b.txt"}


def test_report_csv_empty_has_header_only(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r_csv_empty.db") as idx:
        # No data => no duplicates
        out = tmp_path / "empty.csv"
        report = ReportService(idx)

        written = report.write_duplicates(out, fmt="csv")
        assert written == out

        rows = list(csv.reader(out.read_text(encoding="utf-8").splitlines()))
        # Header should be present even if there are no clusters
        assert rows, "CSV should contain at least a header row when empty"
        header = rows[0]
        assert header == [
            "cluster_id",
            "path",
            "size",
            "mtime_ns",
            "strong_hash",
            "pre_hash",
        ]
        assert rows[1:] == []  # no data rows


def test_report_csv_with_clusters(tmp_path: Path):
    with SQLiteIndex(tmp_path / "r_csv.db") as idx:
        _seed(idx)

        out = tmp_path / "dupes.csv"
        report = ReportService(idx)

        written = report.write_duplicates(out, fmt="csv")
        assert written == out

        # Parse CSV and assert rows
        with open(out, newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)

        # Expect exactly 2 rows (a.txt and b.txt), both in cluster_id=1
        assert len(rows) == 2
        assert {r["path"] for r in rows} == {"a.txt", "b.txt"}
        # cluster_id is string from CSV
        assert set(r["cluster_id"] for r in rows) == {"1"}
