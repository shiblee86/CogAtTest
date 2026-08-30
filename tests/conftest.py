import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

from .cdp import CDPSession

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROME_CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _chrome_binary():
    # CI installs Chrome via an action (e.g. browser-actions/setup-chrome)
    # that does NOT put a conventionally-named binary on PATH -- it only
    # exposes a chrome-path step output. Exporting that into CHROME_PATH
    # (or CHROME_BIN, the other common convention) lets this work in CI
    # without hardcoding any particular action's install location here.
    for var in ("CHROME_PATH", "CHROME_BIN"):
        path = os.environ.get(var)
        if path and Path(path).is_file():
            return path
    for name in CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    pytest.skip("No headless-capable Chrome/Chromium binary found (checked CHROME_PATH/CHROME_BIN and PATH)")


@pytest.fixture(scope="session")
def http_server():
    """Serves the repo root (index.html, app.js, styles.css, assets/) over plain HTTP."""
    port = _free_port()
    proc = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + "/index.html", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("static file server did not come up")
    yield base_url
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def chrome_devtools(tmp_path_factory):
    """Launches one headless Chrome for the whole test session; tests get isolated tabs."""
    binary = _chrome_binary()
    port = _free_port()
    profile_dir = tmp_path_factory.mktemp("chrome-profile")
    proc = subprocess.Popen(
        [
            binary,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1280,1400",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    devtools_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            urllib.request.urlopen(devtools_url + "/json/version", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("headless chrome did not come up")
    yield devtools_url
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture()
def page(chrome_devtools, http_server):
    """A fresh browser tab, navigated to the app, for a single test.

    All tabs share one headless-Chrome user-data-dir (started once per test
    session for speed), which means they'd otherwise share localStorage too.
    Every test gets its own tab, but tabs on the same origin still share
    storage -- so each tab clears it and reloads before the test body runs,
    guaranteeing a clean `state` (mastery/stats/mistakes/daily mission) with
    no cross-test bleed-through.
    """
    # Modern Chrome requires PUT (not GET) for /json/new.
    req = urllib.request.Request(chrome_devtools + "/json/new", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    session = CDPSession(tab["webSocketDebuggerUrl"])
    session.navigate(http_server + "/index.html")
    session.evaluate("localStorage.clear(); true")
    session.navigate(http_server + "/index.html")
    try:
        yield session, http_server
    finally:
        session.close()
        try:
            urllib.request.urlopen(chrome_devtools + f"/json/close/{tab['id']}")
        except Exception:
            pass


def pytest_configure(config):
    for marker in ("unit", "integration", "regression"):
        config.addinivalue_line("markers", f"{marker}: {marker} test suite")
