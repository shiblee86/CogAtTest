"""Integration tests for the home screen: SUBTESTS data, PHOTO_CARDS wiring,
mastery header counters, and the daily mission all have to agree with each
other through the DOM renderHome() actually produces.
"""
import json

import pytest

pytestmark = pytest.mark.integration


def test_home_screen_renders_exactly_one_card_per_subtest(page):
    session, _ = page
    card_ids = json.loads(session.evaluate(
        "JSON.stringify(Array.from(document.querySelectorAll('.subtest-card')).map(c => c.dataset.id))"
    ))
    expected_ids = json.loads(session.evaluate("JSON.stringify(SUBTESTS.map(s => s.id))"))
    assert sorted(card_ids) == sorted(expected_ids)
    assert len(card_ids) == len(set(card_ids)), "no duplicate cards"


def test_every_card_gets_has_photo_class_exactly_when_its_id_is_in_photo_cards(page):
    session, _ = page
    cards = json.loads(session.evaluate(
        """
        JSON.stringify(Array.from(document.querySelectorAll('.subtest-card')).map(c => ({
          id: c.dataset.id,
          hasPhoto: c.classList.contains('has-photo'),
        })))
        """
    ))
    photo_cards = set(json.loads(session.evaluate("JSON.stringify(Array.from(PHOTO_CARDS))")))
    assert photo_cards, "PHOTO_CARDS should not be empty"
    for card in cards:
        assert card["hasPhoto"] == (card["id"] in photo_cards), card


def test_header_shows_zero_mastered_of_fourteen_total_on_a_fresh_profile(page):
    session, _ = page
    assert session.evaluate("document.getElementById('masteredCount').textContent") == "0"
    assert session.evaluate("document.getElementById('totalSubtests').textContent") == "14"


def test_daily_mission_always_picks_exactly_three_subtests(page):
    session, _ = page
    assert session.evaluate("document.querySelectorAll('#missionTasks .dm-task').length") == 3


def test_every_card_shows_play_status_by_default(page):
    session, _ = page
    statuses = json.loads(session.evaluate(
        "JSON.stringify(Array.from(document.querySelectorAll('.subtest-card .sc-status')).map(el => el.textContent))"
    ))
    assert len(statuses) == 14
    assert all("PLAY" in s for s in statuses)


def test_clicking_a_card_opens_its_study_guide(page):
    session, _ = page
    st_id = session.evaluate("SUBTESTS[0].id")
    st_name = session.evaluate("SUBTESTS[0].name")
    session.click(f'.subtest-card[data-id="{st_id}"]')
    heading = session.evaluate("document.querySelector('#detailView .panel-head h2').textContent")
    assert st_name in heading
    assert session.evaluate("document.getElementById('homeView').classList.contains('hidden')") is True
