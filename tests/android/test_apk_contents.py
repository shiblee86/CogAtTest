"""Verifies the *actually built* APK contains what MainActivity expects to
find at runtime (file:///android_asset/index.html and its relative
references) -- complementary to test_asset_sync.py, which only checks the
source tree that gets packaged, not the packaging step itself.
"""
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.android

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _apk_names(debug_apk):
    with zipfile.ZipFile(debug_apk) as z:
        return set(z.namelist())


def test_apk_contains_compiled_code(debug_apk):
    assert "classes.dex" in _apk_names(debug_apk)


def test_apk_bundles_the_web_app_entry_points(debug_apk):
    names = _apk_names(debug_apk)
    for expected in ("assets/index.html", "assets/app.js", "assets/styles.css"):
        assert expected in names, f"{expected} missing from the built APK"


def test_apk_bundles_every_card_artwork_image(debug_apk):
    root_pngs = {p.name for p in (REPO_ROOT / "assets").glob("*.png")}
    names = _apk_names(debug_apk)
    apk_pngs = {Path(n).name for n in names if n.startswith("assets/assets/") and n.endswith(".png")}
    assert apk_pngs == root_pngs
