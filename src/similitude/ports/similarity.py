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

from abc import ABC, abstractmethod
from typing import Iterable, Tuple


class SimilarityPort(ABC):
    """Abstract interface for similarity comparisons."""

    @abstractmethod
    def compare(self, file_a: bytes, file_b: bytes) -> float:
        """Return similarity score between two files (0.0–1.0)."""
        raise NotImplementedError

    @abstractmethod
    def bulk_compare(self, files: Iterable[bytes]) -> Iterable[Tuple[int, int, float]]:
        """Return similarity edges between many files."""
        raise NotImplementedError
