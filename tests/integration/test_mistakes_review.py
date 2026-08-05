"""Integration test for the mistake-recording -> Review Mistakes loop:
a wrong quiz answer should surface a "Review N Mistakes" button on the
Study screen, and answering that restored question correctly should
resolve (remove) the recorded mistake.
"""
import pytest

from ..helpers import answer_correctly, answer_wrong, open_subtest_and_start

pytestmark = pytest.mark.integration


def test_review_flow_resolves_a_recorded_mistake_when_answered_correctly(page):
    session, _ = page
    st_id = open_subtest_and_start(session, 0, "quizBtn")
    answer_wrong(session)
    session.click("#exitBtn")

    # Re-open the same subtest's study guide; it should now offer a review button.
    session.click(f'.subtest-card[data-id="{st_id}"]')
    review_text = session.evaluate("document.getElementById('reviewBtn')?.textContent")
    assert review_text is not None
    assert "1" in review_text

    session.click("#reviewBtn")
    assert session.evaluate("session.mode") == "review"

    answer_correctly(session)
    mistakes_left = session.evaluate(f"state.mistakes.filter(m => m.subtestId === {st_id!r}).length")
    assert mistakes_left == 0


def test_study_screen_has_no_review_button_with_zero_mistakes(page):
    session, _ = page
    st_id = session.evaluate("SUBTESTS[0].id")
    session.click(f'.subtest-card[data-id="{st_id}"]')
    assert session.evaluate("document.getElementById('reviewBtn')") is None
