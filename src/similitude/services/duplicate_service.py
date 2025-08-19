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

from typing import Iterable, Sequence, Dict, Any
from ..ports.index import IndexPort


class DuplicateService:
    """
    Produces exact-duplicate clusters based on the strong hash.
    """

    def __init__(self, index: IndexPort) -> None:
        self._index = index


    def clusters(self) -> Iterable[Sequence[Dict[str, Any]]]:
        """
        Return an iterable of duplicate clusters.
        Each cluster is a sequence of file dicts (metadata + paths).

        Notes:
          * The IndexPort is responsible for efficient grouping.
          * Service may sort members for deterministic output.
        """
        for cluster in self._index.find_duplicates():
            # Ensure derterministic order by path if adapter didn't already 
            yield sorted(cluster, key=lambda r: (r.get("path") or "", r.get("id") or 0))
        
      
