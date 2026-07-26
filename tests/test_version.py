import pytest

from core.version import VERSION, __version__, display_version, is_newer_version


def test_version_has_semantic_format():
    assert __version__ == "0.1.0"
    assert VERSION == (0, 1, 0)


def test_display_version():
    assert display_version() == "Teggy 0.1.0"


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("0.1.1", "0.1.0", True),
        ("0.2.0", "0.1.9", True),
        ("1.0.0", "0.99.99", True),
        ("v0.1.0", "0.1.0", False),
        ("0.1.0", "0.1.1", False),
    ],
)
def test_is_newer_version(candidate, current, expected):
    assert is_newer_version(candidate, current) is expected


@pytest.mark.parametrize("value", ["", "1", "1.2", "1.2.3.4", "1.2.beta"])
def test_is_newer_version_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        is_newer_version(value)
