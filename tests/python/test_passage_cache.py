"""Passages are fetched from CTS once and shared by the norm and lemma pipelines.

`normierowasch` and `lemmatisierowasch` annotate the very same passages, so the
slow CTS request must happen only once per document and run.
"""

import importlib
import os

import pytest

import lemmatisierowasch
import normierowasch

CACHE_DIR = "passagecache"
URN = "urn:cts:dsb:doc1"
OTHER_URN = "urn:cts:dsb:doc2"
WODA = '<text><w norm="WODA" lemma="WODA">woda</w></text>'
DOM = '<text><w norm="DOM" lemma="DOM">dom</w></text>'


@pytest.fixture(autouse=True)
def shared_datadir(tmp_path, monkeypatch):
    """Both pipelines read and write the same data dir, as they do in production."""
    for module in (normierowasch, lemmatisierowasch):
        monkeypatch.setattr(module, "datadir", str(tmp_path) + os.sep)
        monkeypatch.setattr(module, "copyrighttoken", "testtoken")
        module.bagofwords.update({"woda": 1, "dom": 1})
    # Non-empty endpoint keeps lemmatisierowasch.requestctsurl off the network.
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    yield
    normierowasch.bagofwords.clear()
    normierowasch.normbag.clear()
    lemmatisierowasch.bagofwords.clear()
    lemmatisierowasch.lemmabag.clear()


def rows(text):
    """Split tab-separated text into column lists so empty columns stay visible."""
    return [line.split("\t") for line in text.splitlines()]


def serve(monkeypatch, module, passage):
    monkeypatch.setattr(module, "cts_passage", lambda urn, params: passage)


def refuse(monkeypatch, module):
    def fail(urn, params):
        raise AssertionError("passage of " + urn + " was fetched a second time")

    monkeypatch.setattr(module, "cts_passage", fail)


def cached_files(tmp_path):
    cache = tmp_path / CACHE_DIR
    return sorted(os.listdir(cache)) if cache.exists() else []


def test_normmapping_stores_the_fetched_passage(tmp_path, monkeypatch):
    serve(monkeypatch, normierowasch, WODA)

    normierowasch.normmapping(URN)

    files = cached_files(tmp_path)
    assert len(files) == 1
    assert (tmp_path / CACHE_DIR / files[0]).read_text(encoding="utf8") == WODA


def test_lemmamapping_reuses_the_passage_stored_by_normmapping(monkeypatch):
    serve(monkeypatch, normierowasch, WODA)
    normierowasch.normmapping(URN)
    refuse(monkeypatch, lemmatisierowasch)

    result = lemmatisierowasch.lemmamapping(URN)

    assert rows(result) == [["woda", "|WODA|", "", ""]]


def test_mapping_refetches_when_the_cached_passage_was_deleted(tmp_path, monkeypatch):
    serve(monkeypatch, normierowasch, WODA)
    normierowasch.normmapping(URN)
    for name in cached_files(tmp_path):
        os.remove(tmp_path / CACHE_DIR / name)
    serve(monkeypatch, lemmatisierowasch, DOM)

    result = lemmatisierowasch.lemmamapping(URN)

    assert rows(result) == [["dom", "|DOM|", "", ""]]


def test_each_document_is_cached_separately(monkeypatch):
    serve(monkeypatch, normierowasch, WODA)
    normierowasch.normmapping(URN)
    serve(monkeypatch, lemmatisierowasch, DOM)

    result = lemmatisierowasch.lemmamapping(OTHER_URN)

    assert rows(result) == [["dom", "|DOM|", "", ""]]


def test_restricted_response_is_not_cached(tmp_path, monkeypatch):
    serve(monkeypatch, normierowasch, "Error code 7: Unauthorized Access")

    normierowasch.normmapping(URN)

    assert cached_files(tmp_path) == []


def test_unavailable_endpoint_is_not_cached(tmp_path, monkeypatch):
    def fail(urn, params):
        raise OSError("endpoint unavailable")

    monkeypatch.setattr(normierowasch, "cts_passage", fail)

    with pytest.raises(OSError):
        normierowasch.normmapping(URN)

    assert cached_files(tmp_path) == []


def test_setup_removes_the_cache_of_the_previous_run(datadir, monkeypatch):
    import setup

    importlib.reload(setup)
    monkeypatch.setattr(setup, "run", lambda cmd: None)
    stale = os.path.join(datadir, CACHE_DIR, "urn_#_cts_#_dsb_#_doc1.txt")
    os.makedirs(os.path.dirname(stale))
    with open(stale, "w", encoding="utf8") as out:
        out.write(WODA)

    original_cwd = os.getcwd()
    config_path = os.path.join(os.path.dirname(setup.__file__), "config.py")
    config_existed = os.path.exists(config_path)
    try:
        setup.main(["dsb", "0"])
    finally:
        os.chdir(original_cwd)
        if not config_existed and os.path.exists(config_path):
            os.remove(config_path)

    assert not os.path.exists(stale)
