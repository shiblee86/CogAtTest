"""The Android build does NOT read index.html/app.js/styles.css/assets/ from
the repo root -- it only sees whatever was last copied into
android/app/src/main/assets/ (see android/sync-assets.sh). That makes drift
a real, silent failure mode: edit app.js, forget to re-sync, and the Android
app quietly ships stale logic while every other test (which drives the real
root files) keeps passing. These tests exist specifically to catch that.
"""
import hashlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.android

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLED = REPO_ROOT / "android" / "app" / "src" / "main" / "assets"

SYNCED_ROOT_FILES = ["index.html", "app.js", "styles.css"]


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("filename", SYNCED_ROOT_FILES)
def test_bundled_file_matches_repo_root_exactly(filename):
    root_file = REPO_ROOT / filename
    bundled_file = BUNDLED / filename
    assert bundled_file.exists(), (
        f"{filename} missing from android/app/src/main/assets -- "
        f"run android/sync-assets.sh"
    )
    assert _sha256(root_file) == _sha256(bundled_file), (
        f"android/app/src/main/assets/{filename} is out of sync with the repo "
        f"root. Run ./android/sync-assets.sh and rebuild the APK."
    )


def test_bundled_card_artwork_matches_repo_root_exactly():
    root_pngs = {p.name: p for p in (REPO_ROOT / "assets").glob("*.png")}
    bundled_pngs = {p.name: p for p in (BUNDLED / "assets").glob("*.png")}

    assert bundled_pngs.keys() == root_pngs.keys(), (
        f"asset filename mismatch between root assets/ ({sorted(root_pngs)}) "
        f"and the android bundle ({sorted(bundled_pngs)}). "
        f"Run ./android/sync-assets.sh."
    )
    stale = [name for name in root_pngs if _sha256(root_pngs[name]) != _sha256(bundled_pngs[name])]
    assert not stale, f"these images are stale in the android bundle: {stale}"
