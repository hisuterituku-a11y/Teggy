import json
from io import BytesIO
from urllib.error import URLError

import pytest

from core.update_checker import ReleaseInfo, UpdateCheckError, check_for_updates


class FakeResponse:
    def __init__(self, payload):
        self._stream = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self._stream.read()


def make_opener(payload):
    def opener(request, timeout):
        assert request.full_url.endswith("/releases/latest")
        assert timeout == 5.0
        assert request.headers["User-agent"].startswith("Teggy/")
        return FakeResponse(payload)

    return opener


def test_check_for_updates_parses_latest_release():
    release = check_for_updates(
        opener=make_opener(
            {
                "tag_name": "v2.2.0",
                "name": "Teggy 2.2.0",
                "html_url": "https://github.com/example/releases/tag/v2.2.0",
                "body": "Исправления и новые функции",
                "prerelease": False,
            }
        )
    )

    assert release == ReleaseInfo(
        version="2.2.0",
        name="Teggy 2.2.0",
        page_url="https://github.com/example/releases/tag/v2.2.0",
        notes="Исправления и новые функции",
        is_prerelease=False,
    )
    assert release.is_update_available is True


def test_same_release_is_not_an_update():
    release = check_for_updates(
        opener=make_opener(
            {
                "tag_name": "v2.1.0-dev",
                "html_url": "https://github.com/example/releases/tag/v2.1.0-dev",
            }
        )
    )

    assert release.is_update_available is False


def test_network_error_is_wrapped():
    def failing_opener(request, timeout):
        raise URLError("offline")

    with pytest.raises(UpdateCheckError, match="связаться"):
        check_for_updates(opener=failing_opener)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"tag_name": "latest", "html_url": "https://example.com/release"},
        {"tag_name": "v2.2.0", "html_url": "http://example.com/release"},
    ],
)
def test_invalid_release_payload_is_rejected(payload):
    with pytest.raises(UpdateCheckError):
        check_for_updates(opener=make_opener(payload))
