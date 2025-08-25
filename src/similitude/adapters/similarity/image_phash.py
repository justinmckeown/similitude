# Licensed under the Apache License, Version 2.0
from __future__ import annotations
import logging
import math
from typing import Optional, BinaryIO
from pathlib import Path

from ...ports.similarity import SimilarityPort
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePHash(SimilarityPort):
    """
    64-bit perceptual hash (DCT-based). Returns 16-char hex string, or None if not an image / not supported.
    """

    def name(self) -> str:
        return "phash"

    def phash_for_image(self, path: str) -> Optional[str]:
        p = Path(path)
        # quick extension check (cheap guard; prevents opening everything with Pillow)
        if p.suffix.lower() not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
            ".tiff",
            ".webp",
        }:
            return None

        with Image.open(p) as im:
            # Convert to 32x32 grayscale, do DCT, take top-left 8x8 excluding DC, then threshold
            im = im.convert("L").resize((32, 32), Image.Resampling.LANCZOS)  # type: ignore[attr-defined]
            # naive DCT via Pillow's built-ins is not available; implement small DCT-II
            coeffs = self._dct_2d(im.load())
            # take 8x8 block from top-left (including DC); compute median excluding (0,0)
            block = [coeffs[v][u] for v in range(8) for u in range(8)]
            dc, rest = block[0], block[1:]
            median = sorted(rest)[len(rest) // 2]
            bits = 0
            for i, cval in enumerate(rest):
                bits |= (1 if cval > median else 0) << i
            # 63 bits → pad to 64 by including DC > median?
            bits = (bits << 1) | (1 if dc > median else 0)
            return f"{bits:016x}"

    def ssdeep_for_stream(self, stream: BinaryIO) -> Optional[str]:
        # TODO: Impliment this method properly
        return None  # not handled here

    def _dct_2d(self, px):
        N = 32
        vals = [[px[x, y] for x in range(N)] for y in range(N)]
        out = [[0.0] * N for _ in range(N)]
        c = [1 / (2**0.5)] + [1.0] * (N - 1)
        for u in range(N):
            for v in range(N):
                s = 0.0
                for x in range(N):
                    for y in range(N):
                        s += (
                            vals[y][x]
                            * math.cos(((2 * x + 1) * u * math.pi) / (2 * N))
                            * math.cos(((2 * y + 1) * v * math.pi) / (2 * N))
                        )
                out[v][u] = 0.25 * c[u] * c[v] * s
        return out
