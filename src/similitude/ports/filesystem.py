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
from pathlib import Path
from typing import Iterator


class FilesystemPort(ABC):
    """Abstract interface for filesystem access."""

    @abstractmethod
    def walk(self, root: Path) -> Iterator[Path]:
        """Recursively yield file paths under the given root."""
        raise NotImplementedError

    @abstractmethod
    def stat(self, path: Path) -> dict:
        """Return metadata (size, mtime, ctime, inode/fileid) for a given path."""
        raise NotImplementedError

    @abstractmethod
    def open_bytes(self, path: Path, chunk_size: int = 65536) -> Iterator[bytes]:
        """Yield file bytes in chunks for hashing."""
        raise NotImplementedError
