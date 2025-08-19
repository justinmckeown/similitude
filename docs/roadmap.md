# Similitude Roadmap

## 🏗️ Layered Architecture for Similitude

### Layer 1 – Core (MVP)
*Exact, safe, foundational.*
- **File scanner**: recursively traverse drives, apply filters (ignore rules, extensions, size thresholds).
- **Hashing pipeline**:
  - *Fast pre-hash* (size + partial hash) → candidate groups.
  - *Strong hash* (full SHA-256) → confirm duplicates.
- **Local index storage**: SQLite DB with file metadata (`path, size, mtime, hash`).
- **Duplicate detection**: deterministic grouping by hash.
- **CLI interface**: commands for scan, status, and report (CSV/JSON).

---

### Layer 2 – Similarity Beyond Hash
*Start moving from duplicates → near-duplicates.*
- **Perceptual hashes** (pHash, aHash) for images/audio/video.
- **Fuzzy text hashing** (ssdeep, simhash, shingles).
- **Cluster builder**: group files by similarity scores, not just exact hashes.
- **Confidence scores**: probabilistic similarity edges (e.g. “90% similar”).

---

### Layer 3 – Distributed Indexing
*Scale across machines and networks.*
- **Local agents** build & maintain indexes.
- **Index merging**: upload/sync indexes to central service or exchange peer-to-peer.
- **Query federation**: search across multiple indexes (“Do these 500 hashes appear anywhere on the network?”).
- **Data estate view**: consolidated intelligence across all storage.

---

### Layer 4 – Temporal Intelligence
*Understand evolution, not just duplication.*
- **Lineage graph**: model relationships between versions (edges = similarity over time).
- **File provenance tracking**: original vs. modified versions.
- **Temporal snapshots**: how duplicate/near-duplicate sets change across time.
- **Audit and reproducibility**: support for compliance and research data management.

---

### Layer 5 – Policy & Human-in-the-Loop
*Turn intelligence into safe, actionable outcomes.*
- **Action manifests**: human-readable recommendations (link, move, deduplicate).
- **Simulation mode**: show “what would happen” without executing changes.
- **Safe deletion workflows**: highlight redundant files, but never auto-delete.
- **Integrations**: export reports to enterprise workflows (ticketing, compliance tools).

---

## 🎯 Key Design Philosophy
- **SOLID from the start**: each layer is modular, swappable, and testable.
- **Human-first**: the tool informs and supports — it never acts destructively by default.
- **Scalable intelligence**: begins as a simple duplicate finder, evolves into a research-grade data intelligence platform.
