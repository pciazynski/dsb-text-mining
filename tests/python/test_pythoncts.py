import pytest

import pythoncts


class FakeResponse:
    def __init__(self, lines):
        self._lines = lines

    def __iter__(self):
        return iter(self._lines)


# ---------------------------------------------------------------- retry logic


def test_returns_on_first_success(monkeypatch, no_sleep):
    monkeypatch.setattr(
        pythoncts, "urlopen", lambda url, timeout: FakeResponse([b"ok\n"])
    )
    result = pythoncts.urlopenWithRetry("http://example.test/x")
    assert list(result) == [b"ok\n"]
    assert no_sleep == []


def test_retries_then_succeeds(monkeypatch, no_sleep):
    attempts = []

    def flaky(url, timeout):
        attempts.append(url)
        if len(attempts) < 3:
            raise OSError("boom")
        return FakeResponse([b"ok\n"])

    monkeypatch.setattr(pythoncts, "urlopen", flaky)
    result = pythoncts.urlopenWithRetry("http://example.test/x", wait_seconds=7)
    assert list(result) == [b"ok\n"]
    assert len(attempts) == 3
    assert no_sleep == [7, 7]  # slept between the failed attempts


def test_raises_last_error_after_exhausting_retries(monkeypatch, no_sleep):
    attempts = []

    def always_fails(url, timeout):
        attempts.append(url)
        raise OSError("failure " + str(len(attempts)))

    monkeypatch.setattr(pythoncts, "urlopen", always_fails)
    with pytest.raises(OSError, match="failure 4"):
        pythoncts.urlopenWithRetry("http://example.test/x", retries=4)
    assert len(attempts) == 4
    assert len(no_sleep) == 3  # no sleep after the final attempt


def test_timeout_is_forwarded(monkeypatch):
    seen = {}

    def capture(url, timeout):
        seen["timeout"] = timeout
        return FakeResponse([])

    monkeypatch.setattr(pythoncts, "urlopen", capture)
    pythoncts.urlopenWithRetry("http://example.test/x", timeout=42)
    assert seen["timeout"] == 42


# ------------------------------------------------------------ URL construction


@pytest.fixture
def capture_requests(monkeypatch, reset_cts_globals):
    """Route CTS requests to a fake endpoint and record requested URLs."""
    urls = []

    def fake(url, retries=None, wait_seconds=None, timeout=None):
        urls.append(url)
        return FakeResponse([b"payload\n"])

    monkeypatch.setattr(pythoncts, "urlopenWithRetry", fake)
    pythoncts.cts_setmanualurl("http://endpoint.test/")
    return urls


def test_cts_bagofwords_url(capture_requests):
    result = pythoncts.cts_bagofwords("urn:cts:dsb:doc1")
    assert capture_requests == [
        "http://endpoint.test/tm/bagofwords.php?urn=urn:cts:dsb:doc1&sort&lowercase"
    ]
    assert result == "payload"


def test_cts_bagofwords_prepends_ampersand_to_params(capture_requests):
    pythoncts.cts_bagofwords("urn:cts:dsb:doc1", params="sort")
    assert capture_requests[-1].endswith("?urn=urn:cts:dsb:doc1&sort")


def test_cts_passage_url(capture_requests):
    pythoncts.cts_passage("urn:cts:dsb:doc1:1.1")
    assert capture_requests == [
        "http://endpoint.test/plain/passage.php?urn=urn:cts:dsb:doc1:1.1&deletexml"
    ]


# --------------------------------------------------- namespace resolution cache


def test_namespace_resolved_once_and_cached(monkeypatch, reset_cts_globals):
    resolved = []

    def fake_nsurl(ns):
        resolved.append(ns)
        pythoncts.ctsurl = "http://resolved.test/" + ns + "/"

    monkeypatch.setattr(pythoncts, "cts_nsurl", fake_nsurl)
    pythoncts.cts_checkConfig("urn:cts:dsb:doc1")
    pythoncts.cts_checkConfig("urn:cts:dsb:doc2")
    assert resolved == ["dsb"]  # second call served from cache via oldns

    pythoncts.cts_checkConfig("urn:cts:hsb:doc1")
    assert resolved == ["dsb", "hsb"]  # namespace change invalidates the cache
    assert pythoncts.ctsurl == "http://resolved.test/hsb/"


def test_manual_url_bypasses_namespace_resolution(monkeypatch, reset_cts_globals):
    def fail_nsurl(ns):  # pragma: no cover - must never run
        raise AssertionError("namespace resolver should not be contacted")

    monkeypatch.setattr(pythoncts, "cts_nsurl", fail_nsurl)
    pythoncts.cts_setmanualurl("http://endpoint.test/")
    pythoncts.cts_checkConfig("urn:cts:dsb:doc1")
