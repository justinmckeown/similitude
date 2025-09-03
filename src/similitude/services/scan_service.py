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
        self._ignore = ignore_patterns or []
        self._fs = fs
        self._pre_hasher = pre_hasher
        self._strong_hasher = strong_hasher
        self._index = index
        self._ignore_patterns = tuple(ignore_patterns or ())
        self._chunk_size = int(chunk_size)

        self._similarity = tuple(similarity_adapters or [])
        self._enable_phash = bool(enable_phash)
        self._enable_ssdeep = bool(enable_ssdeep)

        logger.debug(f"ScanService loaded from: {__file__}")

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
        SMALL_READ_LIMIT = 8 << 20  # 8 MiB

        for path in self._fs.walk(root):
            p = Path(path)

            # FilesystemPort.walk() should already yield files; double-check defensively.
            try:
                if not p.is_file():
                    continue
            except Exception as e:
                logger.warning("ScanService.scan: non-file path %s (%s)", p, e)
                continue

            if self._ignored(p):
                continue

            # 1) Stat via FS port
            try:
                meta = self._fs.stat(p)
            except Exception as e:
                logger.warning("ScanService.scan: stat failed for %s: %s", p, e)
                continue  # unreadable; skip

            # 2) Upsert file row (count as processed once this succeeds).
            try:
                file_id = self._index.upsert_file(meta)
                processed += 1
            except Exception as e:
                logger.warning("ScanService.scan: upsert_file failed for %s: %s", p, e)
                continue  # DB issue; skip this file

            # 3) Hashing (best-effort; errors are non-fatal)
            pre_hash = None
            strong_hash = None
            phash = None
            ssdeep = None

            # Use size from meta if available; otherwise fall back to os.stat
            try:
                size = (
                    int(meta.get("size"))
                    if isinstance(meta, dict) and "size" in meta
                    else p.stat().st_size
                )
            except Exception:
                size = None

            try:
                if size is not None and size <= SMALL_READ_LIMIT:
                    # Small file: read once into memory and feed both hashers
                    try:
                        data = p.read_bytes()
                    except Exception as e:
                        logger.debug(
                            "ScanService.scan: read_bytes failed for %s: %s", p, e
                        )
                        data = None

                    if data is not None:
                        try:
                            from io import BytesIO

                            pre_hash = self._pre_hasher.hash_stream(BytesIO(data))
                        except Exception as e:
                            logger.debug("Pre-hash failed for %s: %s", p, e)

                        try:
                            from io import BytesIO

                            strong_hash = self._strong_hasher.hash_stream(BytesIO(data))
                        except Exception as e:
                            logger.debug("Strong-hash failed for %s: %s", p, e)
                    else:
                        # Fallback to streaming if read_bytes failed
                        try:
                            with open(p, "rb") as fh:
                                pre_hash = self._pre_hasher.hash_stream(fh)
                        except Exception as e:
                            logger.debug("Pre-hash (stream) failed for %s: %s", p, e)

                        try:
                            with open(p, "rb") as fh:
                                strong_hash = self._strong_hasher.hash_stream(fh)
                        except Exception as e:
                            logger.debug("Strong-hash (stream) failed for %s: %s", p, e)
                else:
                    # Large file: stream separately to avoid RAM spikes
                    try:
                        with open(p, "rb") as fh:
                            pre_hash = self._pre_hasher.hash_stream(fh)
                    except Exception as e:
                        logger.debug("Pre-hash (stream) failed for %s: %s", p, e)

                    try:
                        with open(p, "rb") as fh:
                            strong_hash = self._strong_hasher.hash_stream(fh)
                    except Exception as e:
                        logger.debug("Strong-hash (stream) failed for %s: %s", p, e)
            except Exception as e:
                logger.debug("Hashing setup failed for %s: %s", p, e)

            # Perceptual / fuzzy (best-effort and only if enabled).
            # Stop after first adapter that returns a value for each type.
            if self._enable_phash:
                for sim in self._similarity:
                    try:
                        v = sim.phash_for_image(str(p))
                        if v:
                            phash = v
                            break
                    except Exception as e:
                        logger.warning(
                            "ScanService.scan (phash) failed for %s: %s", p, e
                        )

            if self._enable_ssdeep:
                for sim in self._similarity:
                    try:
                        with open(p, "rb") as fh:
                            v = sim.ssdeep_for_stream(fh)
                        if v:
                            ssdeep = v
                            break
                    except Exception as e:
                        logger.warning(
                            "ScanService.scan (ssdeep) failed for %s: %s", p, e
                        )

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
            except Exception as e:
                logger.debug("upsert_hashes failed for %s: %s", p, e)

        return processed
