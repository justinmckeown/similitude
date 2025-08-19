# GitHub Issues Backlog for Similitude

This file contains a ready-to-use backlog of issues.  
Each bullet can be copy-pasted into a GitHub issue title & description.  
Assign them to milestones as indicated.

---

## Milestone 1: Core (MVP)
### Description:
Implement the foundational features of Similitude: file scanning, hashing pipeline, SQLite storage, duplicate detection, and a basic CLI. This establishes the tool as a reliable duplicate finder with safe reporting and structured data handling.

- **Project skeleton**  
  Set up repo layout (`src/`, `tests/`, `docs/`), `pyproject.toml`, linting (`ruff`), typing (`mypy`).

- **File scanner**  
  Recursive traversal with ignore rules (dotfiles, extensions, size caps).

- **Hashing pipeline**  
  Implement pre-hash (size+partial) and strong hash (SHA-256).

- **SQLite repository**  
  Store file metadata & hashes (Repository pattern).

- **Duplicate detection service**  
  Group by strong hash, return clusters.

- **CLI commands**  
  Implement `scan`, `status`, and `report`.

- **Basic test suite**  
  Unit tests for scanner, hashing, DB.

---

## Milestone 2: Similarity Beyond Hash
### Description:
Extend Similitude beyond exact duplicates by adding perceptual and fuzzy hashing. Enable grouping of near-duplicate files (images, audio, text, binaries) with similarity scores. Reports distinguish exact matches from similarity-based clusters.

- **Perceptual hash module**  
  Implement image/audio perceptual hashes (pHash, aHash).

- **Fuzzy hash module**  
  Implement fuzzy hashing for text/binary similarity (ssdeep, simhash).

- **Cluster builder**  
  Group files by similarity thresholds.

- **Similarity confidence scores**  
  Annotate cluster edges with confidence percentages.

- **Extended reports**  
  Show “exact” vs “similar” clusters in reports.

---

## Milestone 3: Distributed Indexing
### Description:
Enable indexing and searching across multiple machines or drives. Support local index export/import, index merging, and query federation. Provide the first steps toward organisation-wide file intelligence and cross-device duplicate detection.

- **Index export/import**  
  JSON dump of SQLite contents.

- **Index merger**  
  Combine multiple indexes into a single view.

- **Query federation**  
  Run criteria across multiple indexes.

- **Networking adapter (basic)**  
  Sync via shared folder or simple HTTP endpoint.

---

## Milestone 4: Temporal Intelligence
### Description:
Move from static duplicates to dynamic lineage tracking. Introduce file provenance analysis, lineage graphs, and snapshot comparisons across time. Support audit and compliance by making the history of file evolution visible.

- **Lineage graph builder**  
  Model relationships between near-matches.

- **Provenance tracking**  
  Identify originals vs. derivatives.

- **Snapshot diffing**  
  Compare state of file clusters across scans.

- **Audit log**  
  Export lineage & changes for compliance.

---

## Milestone 5: Policy & Human-in-the-Loop
### Description:
Transform file intelligence into safe, actionable recommendations. Generate deduplication manifests, simulate actions, and flag candidates for safe deletion. Integrate with enterprise workflows via structured export formats. Ensure all actions remain human-reviewed and non-destructive by default.

- **Action manifest generator**  
  Generate plan for linking/moving/deduplication.

- **Simulation mode**  
  Dry-run of actions without making changes.

- **Safe deletion report**  
  Flag redundant candidates, never auto-delete.

- **Integrations**  
  Export manifests into CSV/JSON for enterprise workflows.
