"""Test package import."""

import stash_cli


def test_import() -> None:
    """Package exposes version and core symbols."""
    assert stash_cli.__version__ == "0.1.0"
    assert stash_cli.__author__ == "Victor Barra"
