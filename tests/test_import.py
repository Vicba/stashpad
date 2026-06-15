"""Test package import."""

import stashpad


def test_import() -> None:
    """Package exposes version and core symbols."""
    assert stashpad.__version__ == "0.1.0"
    assert stashpad.__author__ == "Victor Barra"
