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

import fnmatch
import logging
from pathlib import Path
from typing import Iterable, Optional

from ..ports.filesystem import FilesystemPort
from ..ports.hasher import HasherPort
from ..ports.index import IndexPort
from ..ports.similarity import SimilarityPort

logger = logging.getLogger(__name__)


class ScanService:
    """
    Orchestrates a file-system scan:
      - walks the filesystem
      - computes pre-hash and strong-hash
      - persists file metadata + hashes
      - is idempotent (skips unchanged files where possible — delegated to IndexPort heuristics)

    Note:
      * For now, we open the file twice (once per hash) to keep memory usage low.
      * In a future iteration we may extend FilesystemPort with an `open_binary` method.
    """

    def __init__(
        self,
        fs: FilesystemPort,
        pre_hasher: HasherPort,
        strong_hasher: HasherPort,
        index: IndexPort,
        *,
        ignore_patterns: Optional[Iterable[str]] = None,
        chunk_size: int = 1 << 20,  # 1 MiB (reserved for future streaming tweaks)
        similarity_adapters: Optional[list[SimilarityPort]] = None,
        enable_phash: bool = False,
        enable_ssdeep: bool = False,
    ) -> None:
        self._fs = fs
        self._pre_hasher = pre_hasher
        self._strong_hasher = strong_hasher
        self._index = index
        self._ignore_patterns = tuple(ignore_patterns or ())
        self._chunk_size = int(chunk_size)

        self._similarity = tuple(similarity_adapters or [])
        self._enable_phash = bool(enable_phash)
        self._enable_ssdeep = bool(enable_ssdeep)

        logger.debug("ScanService loaded from:", __file__)

    def _ignored(self, path: Path) -> bool:
        name = str(path)
        for pat in self._ignore_patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False

    def scan(self, root: Path) -> int:
        """
        Scan a directory tree rooted at `root`.
        Returns:
            Number of files processed (inserted or updated in the index).
        """
        root = Path(root)
        processed = 0

        for path in self._fs.walk(root):
            p = Path(path)

            # Optional safety; FilesystemPort.walk() should already yield files.
            try:
                if not p.is_file():
                    continue
            except Exception as e:
                logger.warning(f"ScanService.scan: {e}")
                continue

            if self._ignored(p):
                continue

            # 1) Stat via FS port
            try:
                meta = self._fs.stat(p)
            except Exception as e:
                logger.warning(f"ScanService.scan: {e}")
                continue  # unreadable; skip

            # 2) Upsert file row (count as processed once this succeeds).
            try:
                file_id = self._index.upsert_file(meta)
                processed += 1
            except Exception:
                continue  # DB issue; skip

            # 3) Hashing (non-fatal if it fails)
            pre_hash = None
            strong_hash = None
            phash = None
            ssdeep = None
            try:
                with open(p, "rb") as fh:
                    pre_hash = self._pre_hasher.hash_stream(fh)
            except Exception:
                pass

            try:
                with open(p, "rb") as fh:
                    strong_hash = self._strong_hasher.hash_stream(fh)
            except Exception:
                pass

            # Perceptual / fuzzy (best-effort and only if enabled)
            if self._enable_phash:
                for sim in self._similarity:
                    try:
                        phash = sim.phash_for_image(str(p)) or phash
                    except Exception as e:
                        logger.error(f"ScanService.scan (phash): {e}")
                        pass
            if self._enable_ssdeep:
                for sim in self._similarity:
                    try:
                        with open(p, "rb") as fh:
                            ssdeep = sim.ssdeep_for_stream(fh) or ssdeep
                    except Exception as e:
                        logger.error(f"ScanService.scan (ssdeep): {e}")
                        pass

            # 4) Upsert hashes (best-effort)
            try:
                self._index.upsert_hashes(
                    file_id,
                    {
                        "pre_hash": pre_hash,
                        "strong_hash": strong_hash,
                        "phash": phash,
                        "ssdeep": ssdeep,
                    },
                )
            except Exception:
                pass  # non-fatal

        return processed
