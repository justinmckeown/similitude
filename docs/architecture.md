# 🏗️ Similitude Architecture

Similitude is designed as a **Hexagonal / Clean Architecture** system, following SOLID principles.  
This ensures the project is modular, testable, and extensible as it evolves from exact duplicate detection to full file intelligence.

---

## 🎯 Design Patterns in Use

- **Hexagonal Architecture (Ports & Adapters):**  
  Core logic depends on abstract ports; details are in adapters.  
- **Clean Architecture / Onion Architecture:**  
  Domain at the center, services around it, adapters at the edge.  
- **Strategy Pattern:**  
  Pluggable hashing strategies (SHA-256, perceptual, fuzzy).  
- **Repository Pattern:**  
  Abstract persistence behind an Index port.  
- **Pipeline Pattern:**  
  Hashing stages: pre-hash → strong-hash → optional similarity.  
- **Service Layer:**  
  Encapsulates use-cases (scan, dedup, report).  
- **Dependency Injection:**  
  Ports are injected into services; wiring happens in CLI.

---

## 📂 Repository Layout

```
similitude/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ docs/
│  ├─ roadmap.md
│  ├─ github_issues.md
│  └─ architecture.md
├─ src/
│  └─ similitude/
│     ├─ config.py
│     ├─ logging_config.py
│     ├─ domain/
│     │  ├─ models.py
│     │  └─ errors.py
│     ├─ ports/
│     │  ├─ filesystem.py
│     │  ├─ hasher.py
│     │  ├─ index.py
│     │  └─ similarity.py
│     ├─ services/
│     │  ├─ scan_service.py
│     │  ├─ duplicate_service.py
│     │  ├─ similarity_service.py
│     │  ├─ lineage_service.py
│     │  └─ report_service.py
│     ├─ adapters/
│     │  ├─ fs/local_fs.py
│     │  ├─ hasher/sha256_hasher.py
│     │  ├─ index/sqlite_index.py
│     │  └─ enrichment/ (future metadata extractors)
│     ├─ cli/app.py
│     └─ utils/
│        ├─ concurrency.py
│        └─ platform_ids.py
├─ tests/
│  ├─ unit/
│  └─ integration/
└─ scripts/
```

---

## 🗄️ Data Model

### Core Tables

**files**
- `id PK`
- `device`, `inode_or_fileid`
- `path`, `size`
- `mtime_ns` (required)
- `ctime_ns` (raw OS value; on Windows/APFS ≈ creation, on Linux = inode change)
- `birthtime_ns` (nullable; true creation time when available)
- `owner_id` (nullable; UID/SID)
- `owner_name` (nullable; resolved lazily)
- `seen_at`

**hashes**
- `file_id FK`
- `pre_hash` (fast hash)
- `strong_hash` (SHA-256)
- `phash` (nullable; perceptual hash)
- `ssdeep` (nullable; fuzzy hash)

### Enrichment Table

**file_enrichment**
- `file_id FK`
- `key TEXT` (e.g. `doc.creator`, `pdf.author`, `fs.owner`)
- `value TEXT`
- `source TEXT` (e.g. `ooxml`, `pdf`, `exif`)
- `extracted_at INTEGER`

---

## 🔄 Key Flows

### Scan (idempotent)
1. Walk FS → `FileIdentity` + `FileMeta`.
2. Skip unchanged files `(device,inode,size,mtime_ns)`.
3. Compute `pre_hash` → group candidates.
4. Compute `strong_hash` when needed.
5. Upsert into SQLite with WAL + indices.

### Exact Grouping
- Group by `strong_hash`.
- Return deterministic clusters.

### Similarity (future)
- Compute perceptual/fuzzy hashes where supported.
- Candidate gen by size/type/binning.
- Emit `SimilarityEdge(file_id_a, file_id_b, score, rationale)`.

---

## ⚡ Concurrency & Performance
- `ThreadPoolExecutor` (I/O bound).
- Chunked reads, mmap for large files.
- Bounded queues (back-pressure).
- Rate limiting to avoid I/O thrash.
- Deterministic ordering for reproducibility.

---

## 💻 CLI Commands (MVP)
- `similitude scan PATH [--db PATH]`
- `similitude report duplicates [--db PATH] [--output out.json|csv]`
- `similitude status [--db PATH]`
- `similitude export-index FILE.json` / `import-index FILE.json` (later)

---

## ⚙️ Config & Logging
- **Config**: Pydantic from env/`.env`.
- **Logging**:
  - Human: rich console.
  - Machine: JSON lines.
- **Feature Flags**: `SIM_ENABLE_PHASH`, `SIM_ENABLE_SSDEEP`.

---

## 🧪 Testing Approach
- **Unit tests**: hashers, repo round-trips, grouping.
- **Integration tests**: FS fixtures, end-to-end scan → report.
- **Cross-platform**: handle inode/fileid differences.
- **CI**: Linux, macOS, Windows; Python 3.10–3.12.

---

## 📜 License
Similitude is licensed under the **Apache License 2.0**.  
All code stubs should include the appropriate license header.
