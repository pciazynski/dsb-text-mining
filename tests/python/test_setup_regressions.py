"""Regression tests for known, unfixed bugs in etl/setup.py."""

import importlib
import os


def test_setup_clears_the_actual_error_log(datadir, monkeypatch):
    import setup

    importlib.reload(setup)
    monkeypatch.setattr(setup, "run", lambda cmd: None)

    log = datadir + "_ERROR.txt"
    with open(log, "w", encoding="utf8") as f:
        f.write("stale error\n")

    original_cwd = os.getcwd()
    config_path = os.path.join(os.path.dirname(setup.__file__), "config.py")
    config_existed = os.path.exists(config_path)
    try:
        setup.main(["dsb", "0"])
    finally:
        os.chdir(original_cwd)
        if not config_existed and os.path.exists(config_path):
            os.remove(config_path)

    remaining = open(log, encoding="utf8").read() if os.path.exists(log) else ""
    assert remaining == ""
