"""Unit tests for validateQuestion() -- the contract every question generator
(makeNumberSeries, genFigureAnalogyPool, makeSudoku, ...) is required to
satisfy before a question reaches the UI. safeGenerate() relies on this
throwing for malformed questions so a bad generator gets skipped instead of
locking up the quiz on a broken screen.
"""
import pytest

from ..cdp import JSError

pytestmark = pytest.mark.unit


def test_validate_question_accepts_a_well_formed_question(page):
    session, _ = page
    result = session.evaluate(
        """
        (function(){
          const q = validateQuestion({
            choices: ['a','b','c','d'], correct: 'a',
            explanation: 'because', steps: ['step1','step2'],
          }, 'test-subtest');
          return q.id && q.id.startsWith('q_');
        })()
        """
    )
    assert result is True


def test_validate_question_rejects_missing_correct_answer(page):
    session, _ = page
    with pytest.raises(JSError, match="Missing correct answer"):
        session.evaluate(
            "validateQuestion({choices:['a','b','c','d'], explanation:'e', steps:['1','2']}, 'x')"
        )


def test_validate_question_rejects_fewer_than_four_choices(page):
    session, _ = page
    with pytest.raises(JSError, match="Must have 4 choices"):
        session.evaluate(
            "validateQuestion({choices:['a','b','c'], correct:'a', explanation:'e', steps:['1','2']}, 'x')"
        )


def test_validate_question_rejects_duplicate_choices(page):
    session, _ = page
    with pytest.raises(JSError, match="Duplicate choices"):
        session.evaluate(
            "validateQuestion({choices:['a','a','b','c'], correct:'a', explanation:'e', steps:['1','2']}, 'x')"
        )


def test_validate_question_rejects_correct_answer_not_present_in_choices(page):
    session, _ = page
    with pytest.raises(JSError, match="Correct answer missing from choices"):
        session.evaluate(
            "validateQuestion({choices:['a','b','c','d'], correct:'z', explanation:'e', steps:['1','2']}, 'x')"
        )


def test_validate_question_rejects_missing_explanation(page):
    session, _ = page
    with pytest.raises(JSError, match="Missing explanation"):
        session.evaluate(
            "validateQuestion({choices:['a','b','c','d'], correct:'a', steps:['1','2']}, 'x')"
        )


def test_validate_question_rejects_fewer_than_two_steps(page):
    session, _ = page
    with pytest.raises(JSError, match="Missing steps"):
        session.evaluate(
            "validateQuestion({choices:['a','b','c','d'], correct:'a', explanation:'e', steps:['1']}, 'x')"
        )
