# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import json
from pathlib import Path
from typing import Literal

from ..ports.index import IndexPort
from .duplicate_service import DuplicateService


class ReportService:
    """
    Generates human- and machine-readable reports (CSV/JSON/NDJSON).
    """

    def __init__(self, index: IndexPort) -> None:
        self._index = index

    def write_duplicates(
        self, out: Path, fmt: Literal["csv", "json", "ndjson"] = "json"
    ) -> Path:
        """
        Write an exact-duplicate report to `output_path` in the specified format.

        The report contains clusters; each cluster is a list of file records.
        CSV is flattened with a synthetic cluster_id.

        Returns:
            The path written.
        """
        clusters = list(DuplicateService(self._index).clusters())

        out = Path(out)  # FIXME: don't need this line I think
        out.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            with open(out, "w", encoding="utf-8") as f:
                json.dump(clusters, f, ensure_ascii=False, indent=2)
            return out

        if fmt == "ndjson":
            with open(out, "w", encoding="utf-8") as f:
                for cluster in clusters:
                    f.write(json.dumps(cluster, ensure_ascii=False) + "\n")
            return out

        if fmt == "csv":
            # Flatten clusters: one row per file with cluster_id
            # Choose a stable set of fields (path, size, mtime_ns, strong_hash)
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = None
                cluster_id = 1
                for cluster in clusters:
                    for rec in cluster:
                        row = {
                            "cluster_id": cluster_id,
                            "path": rec.get("path"),
                            "size": rec.get("size"),
                            "mtime_ns": rec.get("mtime_ns"),
                            "strong_hash": rec.get("strong_hash"),
                            "pre_hash": rec.get("pre_hash"),
                        }
                        if writer is None:
                            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                            writer.writeheader()
                        writer.writerow(row)
                    cluster_id += 1
            return out

        raise ValueError(f"Unsupported format: {fmt}")
