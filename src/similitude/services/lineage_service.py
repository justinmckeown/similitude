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

from dataclasses import dataclass
from typing import Iterable

from ..ports.index import IndexPort


@dataclass(frozen=True)
class LineageEdge:
    """
    Represents a directional relationship (A -> B) in a file's evolution.
    Rationale can include timestamps, author hints, or similarity evidence.
    """
    parent_id: int
    child_id: int
    rationale: str = ""


class LineageService:
    """
    Infers simple lineage edges from timestamps + similarity clusters.
    """

    def __init__(self, index: IndexPort) -> None:
        self._index = index

    def build(self) -> Iterable[LineageEdge]:
        """
        Produce tentative lineage edges suitable for human review.

        Notes:
          * Heuristics may include:
            - newer mtime as 'child'
            - shared author/owner hints (if enrichment available)
            - stronger similarity edges as supporting evidence
        """
        # TODO: query index for candidate groups, apply heuristics, yield LineageEdge.
        return []
