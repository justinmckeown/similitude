# tests/unit/test_domain_imports.py
def test_domain_imports():
    import similitude.domain.errors as e

    # touch the classes so coverage includes the module
    assert isinstance(e.SimilitudeError(), Exception)
