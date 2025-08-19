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
from typing import Iterable, Tuple

from ..ports.index import IndexPort
from ..ports.similarity import SimilarityPort


@dataclass(frozen=True)
class SimilarityEdge:
    """Represents a similarity relationship between two files."""
    file_id_a: int
    file_id_b: int
    score: float
    rationale: str = ""  # e.g., "phash", "ssdeep", "size+type bin match"


class SimilarityService:
    """
    Computes near-duplicate relationships using pluggable similarity engines.
    """

    def __init__(self, index: IndexPort, engine: SimilarityPort) -> None:
        self._index = index
        self._engine = engine

    def compute(self, threshold: float = 0.85) -> Iterable[SimilarityEdge]:
        """
        Yield SimilarityEdge entries above the given score threshold.

        Notes:
          * Candidate generation should be delegated to IndexPort (size/type bins)
            to avoid O(N^2) comparisons.
          * This stub intentionally omits implementation details.
        """
        # TODO: fetch candidates from index, run engine.compare/bulk_compare,
        #       filter by threshold, yield SimilarityEdge instances.
        return []
