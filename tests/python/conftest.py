import importlib
import os
import sys

import pytest

import config_def

# Ensure tests are deterministic even when a local, untracked etl/config.py exists.
sys.modules["config"] = config_def


@pytest.fixture(autouse=True)
def stable_config_module(monkeypatch):
    """Force imports of config to resolve to config_def for every test."""
    monkeypatch.setitem(sys.modules, "config", config_def)


@pytest.fixture
def datadir(tmp_path, monkeypatch):
    """Point the ETL data directory at a tmp dir and reload dependent modules."""
    monkeypatch.setenv("DSB_DATADIR", str(tmp_path))
    import settings
    import bagofwords

    importlib.reload(settings)
    importlib.reload(bagofwords)
    bagofwords.doc_year.clear()
    yield settings.datadir
    monkeypatch.delenv("DSB_DATADIR", raising=False)
    importlib.reload(settings)
    importlib.reload(bagofwords)


@pytest.fixture
def reset_cts_globals():
    """Ensure pythoncts module state does not leak between tests."""
    import pythoncts

    pythoncts.ctsurl = ""
    pythoncts.oldns = ""
    pythoncts.manualurl = ""
    yield pythoncts
    pythoncts.ctsurl = ""
    pythoncts.oldns = ""
    pythoncts.manualurl = ""


@pytest.fixture
def write_peryear():
    """Factory writing tiny per-year token/frequency files.

    Usage: write_peryear(base, {1800: {"a": 3, "b": 1}, 1850: {"a": 2}})
    creates <base>peryear/1800.txt etc. and returns the base folder path.
    """

    def _write(base, years):
        base = str(base)
        os.makedirs(base, exist_ok=True)
        peryear = base + "peryear"
        os.makedirs(peryear, exist_ok=True)
        for year, tokens in years.items():
            with open(
                os.path.join(peryear, str(year) + ".txt"), "w", encoding="utf8"
            ) as outf:
                for token, freq in tokens.items():
                    print(token, freq, sep="	", file=outf)
        return base

    return _write


@pytest.fixture
def no_sleep(monkeypatch):
    """Disable real sleeping in retry loops; records call arguments."""
    import pythoncts

    calls = []
    monkeypatch.setattr(pythoncts.time, "sleep", lambda s: calls.append(s))
    return calls
