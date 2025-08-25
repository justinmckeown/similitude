# tests/unit/test_image_phash.py
from pathlib import Path

from PIL import Image

from similitude.adapters.similarity.image_phash import ImagePHash


def _save_image(
    tmp_path: Path, name: str, color: tuple[int, int, int], size=(32, 32)
) -> str:
    p = tmp_path / name
    img = Image.new("RGB", size, color)
    img.save(p, format="PNG")
    return str(p)


def test_phash_basic_and_length(tmp_path: Path):
    path = _save_image(tmp_path, "solid_white.png", (255, 255, 255))
    ph = ImagePHash()
    h = ph.phash_for_image(path)
    assert isinstance(h, str)
    # 64-bit hex → 16 hex chars
    assert len(h) == 16


def test_phash_is_deterministic(tmp_path: Path):
    path = _save_image(tmp_path, "solid_gray.png", (128, 128, 128))
    ph = ImagePHash()
    h1 = ph.phash_for_image(path)
    h2 = ph.phash_for_image(path)
    assert h1 == h2


def test_phash_distinguishes_different_images(tmp_path: Path):
    white = _save_image(tmp_path, "white.png", (255, 255, 255))
    black = _save_image(tmp_path, "black.png", (0, 0, 0))
    ph = ImagePHash()
    h_white = ph.phash_for_image(white)
    h_black = ph.phash_for_image(black)
    # Hashes should differ for very different images
    assert isinstance(h_white, str) and isinstance(h_black, str)
    assert h_white != h_black


def test_phash_handles_non_image_gracefully(tmp_path: Path):
    # Create a text file and ensure the adapter returns None, not an exception
    p = tmp_path / "not_an_image.txt"
    p.write_text("hello, world")
    ph = ImagePHash()
    assert ph.phash_for_image(str(p)) is None
