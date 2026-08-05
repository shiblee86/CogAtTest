"""Integration tests that drive a full study -> quiz/exam -> results loop
through the real UI: clicking a card, starting a session, answering
questions by clicking the actual rendered choice buttons, and checking the
resulting state/DOM/localStorage -- not by calling internal functions
directly.
"""
import pytest

from ..helpers import answer_correctly, answer_wrong, open_subtest_and_start

pytestmark = pytest.mark.integration


def test_quiz_can_be_completed_by_answering_every_question_correctly(page):
    session, _ = page
    quiz_n = session.evaluate("SUBTESTS[0].quizN")
    open_subtest_and_start(session, 0, "quizBtn")

    for _ in range(quiz_n):
        assert session.evaluate("document.querySelectorAll('#choicesGrid .choice-btn').length") == 4
        answer_correctly(session)
        assert "Correct!" in session.evaluate("document.getElementById('feedbackArea').textContent")
        session.click("#nextBtn")

    title = session.evaluate("document.querySelector('.results-card .r-title')?.textContent")
    assert f"{quiz_n}/{quiz_n}" in title
    assert session.evaluate("document.querySelector('.results-card').classList.contains('pass')") is True


def test_passing_an_exam_marks_the_subtest_mastered_immediately_in_the_header(page):
    session, _ = page
    exam_n = session.evaluate("SUBTESTS[0].examN")
    st_id = open_subtest_and_start(session, 0, "examBtn")

    for _ in range(exam_n):
        answer_correctly(session)
        session.click("#nextBtn")

    mastery = session.evaluate(f"state.mastery[{st_id!r}]")
    assert mastery["earned"] is True
    assert mastery["score"] == exam_n
    assert mastery["total"] == exam_n
    assert session.evaluate("document.getElementById('masteredCount').textContent") == "1"


def test_mastery_survives_a_full_page_reload(page):
    session, url = page
    exam_n = session.evaluate("SUBTESTS[0].examN")
    st_id = open_subtest_and_start(session, 0, "examBtn")

    for _ in range(exam_n):
        answer_correctly(session)
        session.click("#nextBtn")

    session.navigate(url + "/index.html")
    assert session.evaluate(f"state.mastery[{st_id!r}]?.earned") is True
    assert session.evaluate("document.getElementById('masteredCount').textContent") == "1"
    card_status = session.evaluate(
        f'document.querySelector(\'.subtest-card[data-id="{st_id}"] .sc-status\').textContent'
    )
    assert "%" in card_status  # mastered cards show a percentage badge, not "PLAY"


def test_answering_a_quiz_question_wrong_shows_wrong_feedback_and_records_a_mistake(page):
    session, _ = page
    st_id = open_subtest_and_start(session, 0, "quizBtn")

    answer_wrong(session)
    feedback = session.evaluate("document.getElementById('feedbackArea').textContent")
    assert "Not quite" in feedback

    mistakes = session.evaluate(f"state.mistakes.filter(m => m.subtestId === {st_id!r}).length")
    assert mistakes == 1


def test_exit_button_during_a_quiz_returns_to_the_home_screen(page):
    session, _ = page
    open_subtest_and_start(session, 0, "quizBtn")
    session.click("#exitBtn")
    assert session.evaluate("document.getElementById('homeView').classList.contains('hidden')") is False
    assert session.evaluate("document.querySelectorAll('.subtest-card').length") == 14
