# Licensed under the Apache License, Version 2.0
from __future__ import annotations

from typing import Protocol, Optional, BinaryIO


class SimilarityPort(Protocol):
    """
    Optional content-aware hashing.
    Implementers may return None when the file isn't supported or on recoverable failure.
    """

    def name(self) -> str: ...

    def phash_for_image(self, path: str) -> Optional[str]:
        """Return a 64-bit perceptual hash for image files as hex, or None."""
        return None  # default no-op

    def ssdeep_for_stream(self, stream: BinaryIO) -> Optional[str]:
        """Return an ssdeep (context-triggered piecewise) fuzzy hash for arbitrary content, or None."""
        return None  # default no-op


# TODO: chekc if these ar eimplimented anywhere. they're left over from when I changed the ABC class to a protocol.

# def compare(self, file_a: bytes, file_b: bytes) -> float:
#    """Return similarity score between two files (0.0–1.0)."""
#    raise NotImplementedError
#
# def bulk_compare(self, files: Iterable[bytes]) -> Iterable[Tuple[int, int, float]]:
#    """Return similarity edges between many files."""
#    raise NotImplementedError
