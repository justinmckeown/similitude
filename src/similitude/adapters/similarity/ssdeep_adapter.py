# Licensed under the Apache License, Version 2.0
from __future__ import annotations

from typing import Optional, BinaryIO

from ...ports.similarity import SimilarityPort

try:
    import ssdeep as _ssdeep  # pip install ssdeep
except Exception:
    _ssdeep = None


class SsdeepAdapter(SimilarityPort):
    def name(self) -> str:
        return "ssdeep"

    def phash_for_image(self, path: str) -> Optional[str]:
        return None

    def ssdeep_for_stream(self, stream: BinaryIO) -> Optional[str]:
        if _ssdeep is None:
            return None
        try:
            h = _ssdeep.Hash()
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                h.update(chunk)
            return h.digest()
        except Exception:
            return None
