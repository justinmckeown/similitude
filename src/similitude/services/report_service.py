# Licensed under the Apache License, Version 2.0 (the "License");
# ...
from __future__ import annotations

import csv
import json
from typing import Iterable, Any, List
from pathlib import Path

from ..ports.index import IndexPort
from .duplicate_service import DuplicateService


class ReportService:
    """
    Generates human- and machine-readable duplicate reports (JSON/NDJSON/CSV).

    Notes:
      - JSON (default): one JSON array of clusters; each cluster is a list of file dicts.
      - NDJSON: one cluster (list of file dicts) per line, as a JSON array.
      - CSV: flattened rows with a synthetic cluster_id; stable column order.
    """

    def __init__(self, index: IndexPort) -> None:
        self._index = index

    def _clusters(self) -> Iterable[list[dict[str, Any]]]:
        # Keep the indirection through DuplicateService for separation of concerns.
        return DuplicateService(self._index).clusters()

    def write_duplicates(self, out: Path, fmt: str = "json") -> Path:
        """
        Write an exact-duplicate report to `out` in the specified format.

        Returns:
            The path written.

        Raises:
            ValueError: if an unsupported format is requested.
        """
        fmt = (fmt or "json").lower()
        clusters: List[List[dict[str, Any]]] = [list(c) for c in self._clusters()]

        out.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            out.write_text(
                json.dumps(clusters, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return out

        if fmt == "ndjson":
            # One cluster (list of dicts) per line
            lines = (json.dumps(cluster, ensure_ascii=False) for cluster in clusters)
            text = "\n".join(lines)
            # Add a trailing newline only if non-empty (cosmetic)
            out.write_text(text + ("\n" if text else ""), encoding="utf-8")
            return out

        if fmt == "csv":
            # Stable schema for downstream tooling
            fieldnames = [
                "cluster_id",
                "path",
                "size",
                "mtime_ns",
                "strong_hash",
                "pre_hash",
            ]
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                # If you prefer an empty file when no clusters, comment out the header line below.
                writer.writeheader()
                cluster_id = 1
                for cluster in clusters:
                    for rec in cluster:
                        writer.writerow(
                            {
                                "cluster_id": cluster_id,
                                "path": rec.get("path"),
                                "size": rec.get("size"),
                                "mtime_ns": rec.get("mtime_ns"),
                                "strong_hash": rec.get("strong_hash"),
                                "pre_hash": rec.get("pre_hash"),
                            }
                        )
                    cluster_id += 1
            return out

        raise ValueError(f"Unsupported format: {fmt}")
