import pytest

from core.version import VERSION, __version__, display_version, is_newer_version


def test_version_matches_current_development_release():
    assert __version__ == "2.1.0-dev"
    assert VERSION == (2, 1, 0)


def test_display_version():
    assert display_version() == "Teggy 2.1.0-dev"


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("2.1.0", "2.1.0-dev", True),
        ("2.1.1", "2.1.0", True),
        ("2.2.0", "2.1.9", True),
        ("3.0.0", "2.99.99", True),
        ("v2.1.0", "2.1.0", False),
        ("2.1.0-dev", "2.1.0", False),
        ("2.1.0", "2.1.1", False),
    ],
)
def test_is_newer_version(candidate, current, expected):
    assert is_newer_version(candidate, current) is expected


@pytest.mark.parametrize(
    "value",
    ["", "1", "1.2", "1.2.3.4", "1.2.beta", "version-2.1.0"],
)
def test_is_newer_version_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        is_newer_version(value)
