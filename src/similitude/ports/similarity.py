# Licensed under the Apache License, Version 2.0
from __future__ import annotations

from typing import Protocol, Optional, BinaryIO


class SimilarityPort(Protocol):
    """
    Optional content-aware hashing.
    Implementers may return None when the file isn't supported or on recoverable failure.
    """

    def name(self) -> str: ...

    # TODO: Implement this method fully
    def phash_for_image(self, path: str) -> Optional[str]:
        """Return a 64-bit perceptual hash for image files as hex, or None."""
        return None  # default no-op

    # TODO: Implement this method fully
    def ssdeep_for_stream(self, stream: BinaryIO) -> Optional[str]:
        """Return an ssdeep (context-triggered piecewise) fuzzy hash for arbitrary content, or None."""
        return None  # default no-op
