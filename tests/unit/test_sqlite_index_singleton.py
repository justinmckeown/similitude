from similitude.adapters.index.sqlite_index import SQLiteIndex

def test_find_duplicates_excludes_singletons(tmp_path):
    db = tmp_path / "test.db"
    index = SQLiteIndex(db)

    # Insert file A and B with same strong hash
    file_meta = {"path": "a.txt", "size": 1, "mtime_ns": 1}
    ida = index.upsert_file(file_meta)
    index.upsert_hashes(ida, {"strong_hash": "same"})

    file_meta["path"] = "b.txt"
    idb = index.upsert_file(file_meta)
    index.upsert_hashes(idb, {"strong_hash": "same"})

    # Insert file C with different strong hash
    file_meta["path"] = "c.txt"
    idc = index.upsert_file(file_meta)
    index.upsert_hashes(idc, {"strong_hash": "different"})

    clusters = list(index.find_duplicates())
    assert len(clusters) == 1
    paths = {rec["path"] for rec in clusters[0]}
    assert paths == {"a.txt", "b.txt"}
