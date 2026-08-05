"""Regression tests for the "cards need illustrated artwork" fix: the
samurai-mascot.png page background, the 14 per-card grid-*.png illustrations,
and the CSS/JS wiring (PHOTO_CARDS -> .has-photo -> background-image) that
connects them. Split into file-based checks (fast, no browser -- catch an
asset getting renamed/deleted or a CSS rule going stale) and one browser
check for the JS<->DOM parity that can only be observed live.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.regression

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
STYLES_CSS = (REPO_ROOT / "styles.css").read_text()
INDEX_HTML = (REPO_ROOT / "index.html").read_text()

# id -> asset filename, exactly as wired in styles.css's per-card rules.
CARD_ASSET_MAP = {
    "divided-shapes": "grid-divided-shapes.png",
    "pic-analogies": "grid-pic-analogies.png",
    "sentence-comp": "grid-sentence-comp.png",
    "pic-classification": "grid-pic-classification.png",
    "fig-analogies": "grid-fig-analogies.png",
    "fig-classification": "grid-fig-classification.png",
    "num-analogies": "grid-num-analogies.png",
    "num-series": "grid-num-series.png",
    "num-puzzles": "grid-num-puzzles.png",
    "abacus-series": "grid-abacus.png",
    "sudoku": "grid-sudoku.png",
    "paper-folding": "grid-paper-folding.png",
    "nested-shapes": "grid-nested-shapes.png",
    "rotating-shapes": "grid-rotating-shapes.png",
}


def test_samurai_mascot_asset_exists():
    assert (ASSETS_DIR / "samurai-mascot.png").is_file()


@pytest.mark.parametrize("card_id,filename", sorted(CARD_ASSET_MAP.items()))
def test_each_photo_card_asset_file_exists_on_disk(card_id, filename):
    assert (ASSETS_DIR / filename).is_file(), f"{card_id} references missing asset {filename}"


@pytest.mark.parametrize("card_id,filename", sorted(CARD_ASSET_MAP.items()))
def test_each_photo_card_has_a_matching_css_background_rule(card_id, filename):
    pattern = rf'\.subtest-card\[data-id="{re.escape(card_id)}"\]\.has-photo\s*\{{[^}}]*url\(\'assets/{re.escape(filename)}\'\)'
    assert re.search(pattern, STYLES_CSS), f"no CSS rule wiring {card_id} to assets/{filename}"


def test_bg_motif_element_present_in_html_and_styled_in_css():
    assert '<div id="bgMotif"' in INDEX_HTML
    assert "#bgMotif" in STYLES_CSS
    assert "samurai-mascot.png" in STYLES_CSS


def test_bg_motif_sits_behind_page_content_not_in_front_of_it():
    """z-index must be negative: a non-negative z-index on a `position:fixed`
    element paints *above* ordinary non-positioned content (like `.app`),
    which would bury the entire UI under the background image.
    """
    match = re.search(r"#bgMotif\s*\{([^}]*)\}", STYLES_CSS)
    assert match, "#bgMotif rule not found"
    rule_body = match.group(1)
    z_index_match = re.search(r"z-index:\s*(-?\d+)", rule_body)
    assert z_index_match, "#bgMotif has no explicit z-index"
    assert int(z_index_match.group(1)) < 0


def test_has_photo_cards_get_a_legible_text_color_override():
    """The scrim gradients are dark; without an explicit light text color,
    the app's default (dark, in light mode) .sc-name/.sc-desc text would be
    unreadable on top of a photo card.
    """
    assert re.search(r"\.subtest-card\.has-photo\s+\.sc-name\s*\{[^}]*color:", STYLES_CSS)
    assert re.search(r"\.subtest-card\.has-photo\s+\.sc-desc\s*\{[^}]*color:", STYLES_CSS)


def test_photo_cards_set_matches_the_card_asset_map_exactly(page):
    """Live-DOM/JS check: PHOTO_CARDS (app.js) must line up exactly with the
    id set this file's CSS-rule checks above assume.
    """
    import json

    session, _ = page
    photo_cards = set(json.loads(session.evaluate("JSON.stringify(Array.from(PHOTO_CARDS))")))
    assert photo_cards == set(CARD_ASSET_MAP.keys())


def test_photo_cards_is_exactly_the_full_subtest_list(page):
    """Every subtest currently ships photo artwork -- if a future subtest is
    added without art, this should fail loudly rather than silently leaving
    an icon-watermark card among photo cards.
    """
    import json

    session, _ = page
    photo_cards = set(json.loads(session.evaluate("JSON.stringify(Array.from(PHOTO_CARDS))")))
    subtest_ids = set(json.loads(session.evaluate("JSON.stringify(SUBTESTS.map(s => s.id))")))
    assert photo_cards == subtest_ids
