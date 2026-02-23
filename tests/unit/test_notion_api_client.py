from __future__ import annotations

import io
import unittest
import urllib.error
from unittest import mock

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from notion_client import NotionAPIClient, NotionAPIError  # noqa: E402


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestNotionAPIClient(unittest.TestCase):
    def test_retries_on_429_respects_retry_after(self):
        sleep_calls: list[float] = []

        err = urllib.error.HTTPError(
            url="https://api.notion.com/v1/pages/x",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "0.01"},
            fp=io.BytesIO(b'{"message":"rate limited"}'),
        )

        client = NotionAPIClient(
            token="test",
            max_attempts=2,
            sleep_fn=lambda s: sleep_calls.append(float(s)),
            rand_fn=lambda: 0.0,
        )

        with mock.patch(
            "notion_client.urllib.request.urlopen",
            side_effect=[err, _FakeResponse('{"ok": true}')],
        ):
            out = client._request_json("GET", "https://api.notion.com/v1/pages/x")

        self.assertEqual(out, {"ok": True})
        self.assertEqual(sleep_calls, [0.01])

    def test_does_not_retry_on_401(self):
        sleep_calls: list[float] = []
        err = urllib.error.HTTPError(
            url="https://api.notion.com/v1/pages/x",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b'{"message":"unauthorized"}'),
        )

        client = NotionAPIClient(
            token="test",
            max_attempts=3,
            sleep_fn=lambda s: sleep_calls.append(float(s)),
            rand_fn=lambda: 0.0,
        )

        with mock.patch("notion_client.urllib.request.urlopen", side_effect=[err]):
            with self.assertRaises(NotionAPIError) as ctx:
                client._request_json("GET", "https://api.notion.com/v1/pages/x")

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(sleep_calls, [])

    def test_retries_on_5xx_with_backoff(self):
        sleep_calls: list[float] = []

        err = urllib.error.HTTPError(
            url="https://api.notion.com/v1/pages/x",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=io.BytesIO(b'{"message":"bad gateway"}'),
        )

        rand_value = 0.5
        client = NotionAPIClient(
            token="test",
            max_attempts=2,
            sleep_fn=lambda s: sleep_calls.append(float(s)),
            rand_fn=lambda: rand_value,
        )

        with mock.patch(
            "notion_client.urllib.request.urlopen",
            side_effect=[err, _FakeResponse('{"ok": true}')],
        ):
            out = client._request_json("GET", "https://api.notion.com/v1/pages/x")

        self.assertEqual(out, {"ok": True})
        # _backoff_seconds(attempt=1): base = 0.8 * (2 ** min(1, 6)) = 1.6
        # jitter = 0.5 * 0.25 * 1.6 = 0.2
        # total = min(20.0, 1.6 + 0.2) = 1.8
        expected_backoff = min(20.0, 0.8 * (2 ** 1) + rand_value * 0.25 * 0.8 * (2 ** 1))
        self.assertEqual(len(sleep_calls), 1)
        self.assertAlmostEqual(sleep_calls[0], expected_backoff)

    def test_retries_on_url_error(self):
        sleep_calls: list[float] = []

        url_err = urllib.error.URLError("connection refused")

        client = NotionAPIClient(
            token="test",
            max_attempts=2,
            sleep_fn=lambda s: sleep_calls.append(float(s)),
            rand_fn=lambda: 0.0,
        )

        with mock.patch(
            "notion_client.urllib.request.urlopen",
            side_effect=[url_err, _FakeResponse('{"result": "success"}')],
        ):
            out = client._request_json("GET", "https://api.notion.com/v1/pages/x")

        self.assertEqual(out, {"result": "success"})
        # sleep_fn was called once for the retry after URLError
        self.assertEqual(len(sleep_calls), 1)
        # _backoff_seconds(attempt=1) with rand_fn=0.0: base=1.6, jitter=0.0, total=1.6
        expected_backoff = min(20.0, 0.8 * (2 ** 1))
        self.assertAlmostEqual(sleep_calls[0], expected_backoff)

