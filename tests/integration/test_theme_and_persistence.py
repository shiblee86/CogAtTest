"""Integration tests for the light/dark theme toggle and its persistence
across a full page reload via localStorage.
"""
import pytest

pytestmark = pytest.mark.integration


def test_app_starts_in_light_mode_on_a_fresh_profile(page):
    session, _ = page
    assert session.evaluate("document.body.classList.contains('dark')") is False
    assert session.evaluate("document.getElementById('themeBtn').textContent") == "🌙 Dark"


def test_clicking_theme_button_toggles_dark_mode_and_its_label(page):
    session, _ = page
    session.click("#themeBtn")
    assert session.evaluate("document.body.classList.contains('dark')") is True
    assert session.evaluate("document.getElementById('themeBtn').textContent") == "☀️ Light"
    assert session.evaluate("document.getElementById('themeBtn').getAttribute('aria-pressed')") == "true"


def test_theme_choice_persists_across_a_reload(page):
    session, url = page
    session.click("#themeBtn")
    assert session.evaluate("document.body.classList.contains('dark')") is True
    session.navigate(url + "/index.html")
    assert session.evaluate("document.body.classList.contains('dark')") is True
    assert session.evaluate("document.getElementById('themeBtn').textContent") == "☀️ Light"
