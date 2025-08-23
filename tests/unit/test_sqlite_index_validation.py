import pytest
from pathlib import Path
from similitude.adapters.index.sqlite_index import SQLiteIndex


def test_upsert_file_requires_minimal_fields(tmp_path: Path):
    db = tmp_path / "val.db"
    with SQLiteIndex(db) as idx:
        # missing size
        with pytest.raises(ValueError):
            idx.upsert_file({"path": "x", "mtime_ns": 1})
        # missing path
        with pytest.raises(ValueError):
            idx.upsert_file({"size": 1, "mtime_ns": 1})
        # missing mtime_ns
        with pytest.raises(ValueError):
            idx.upsert_file({"path": "x", "size": 1})
