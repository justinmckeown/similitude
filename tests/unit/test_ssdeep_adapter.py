# tests/unit/test_ssdeep_adapter.py
from io import BytesIO
import types


import similitude.adapters.similarity.ssdeep_adapter as mod
from similitude.adapters.similarity.ssdeep_adapter import SsdeepAdapter


def test_name():
    assert SsdeepAdapter().name() == "ssdeep"


def test_ssdeep_returns_none_when_backend_missing(monkeypatch):
    # Simulate Windows without ssdeep available
    monkeypatch.setattr(mod, "_ssdeep", None, raising=False)
    adap = SsdeepAdapter()
    out = adap.ssdeep_for_stream(BytesIO(b"abcdef"))
    assert out is None


def test_ssdeep_happy_path_with_fake_backend(monkeypatch):
    # Build a tiny fake ssdeep module just for this test
    digests = []

    class FakeHash:
        def __init__(self):
            self._buf = bytearray()

        def update(self, chunk: bytes):
            # mimic streaming updates
            self._buf.extend(chunk)

        def digest(self) -> str:
            # deterministic "digest" for the test
            digests.append(bytes(self._buf))
            return f"fake:{len(self._buf)}"

    fake = types.SimpleNamespace(Hash=FakeHash)
    monkeypatch.setattr(mod, "_ssdeep", fake, raising=False)

    adap = SsdeepAdapter()
    data = b"A" * 10 + b"B" * 5 + b"C" * 1
    out = adap.ssdeep_for_stream(BytesIO(data))
    assert out == "fake:16"  # length recorded by FakeHash
    # ensure we actually streamed the bytes through
    assert digests and digests[-1] == data


def test_ssdeep_backend_error_returns_none(monkeypatch):
    class BadHash:
        def update(self, chunk: bytes):
            raise RuntimeError("boom")

        def digest(self) -> str:
            return "never"

    fake = types.SimpleNamespace(Hash=lambda: BadHash())
    monkeypatch.setattr(mod, "_ssdeep", fake, raising=False)

    adap = SsdeepAdapter()
    out = adap.ssdeep_for_stream(BytesIO(b"some data"))
    assert out is None
