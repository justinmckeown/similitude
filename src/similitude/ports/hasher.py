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
from typing import BinaryIO


class HasherPort(ABC):
    """Abstract interface for hashing strategies."""

    @abstractmethod
    def hash_stream(self, stream: BinaryIO) -> str:
        """Return hash of the given binary stream as hex string."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the hashing strategy."""
        raise NotImplementedError
