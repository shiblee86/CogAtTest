"""Unit tests for the accuracy/badge scoring math: getAccuracy(), getBadge(),
updateBadges(). These are exercised by writing directly into `state` (the
app's in-memory store) rather than by playing through a quiz, so each
threshold can be tested precisely instead of relying on random question
outcomes.
"""
import pytest

pytestmark = pytest.mark.unit


def test_get_accuracy_is_zero_with_no_recorded_attempts(page):
    session, _ = page
    assert session.evaluate("getAccuracy('never-attempted')") == 0


def test_get_accuracy_rounds_to_the_nearest_percent(page):
    session, _ = page
    session.evaluate("state.stats.attempts['x']=3; state.stats.correct['x']=2; true")
    # 2/3 = 66.67% -> rounds to 67
    assert session.evaluate("getAccuracy('x')") == 67


@pytest.mark.parametrize(
    "attempts,correct,expected_badge",
    [
        (5, 5, "gold"),    # acc 100% & attempts>=5 -> gold (acc>=90 & attempts>=5)
        (4, 3, "silver"),  # acc 75% & attempts>=3, but attempts<5 so gold is unreachable -> silver
        (2, 1, "bronze"),  # acc 50% & attempts>=2, below silver's 70% floor -> bronze
        (1, 1, None),      # acc 100% but only 1 attempt, below bronze's attempts>=2 floor -> no badge
    ],
)
def test_update_badges_awards_the_expected_tier(page, attempts, correct, expected_badge):
    session, _ = page
    st_id = session.evaluate("SUBTESTS[0].id")
    session.evaluate(
        f"state.stats.attempts[{st_id!r}]={attempts}; state.stats.correct[{st_id!r}]={correct}; "
        "updateBadges(); true"
    )
    badge = session.evaluate(f"getBadge({st_id!r})")
    assert badge == expected_badge


def test_update_badges_gives_no_badge_below_bronze_threshold(page):
    session, _ = page
    st_id = session.evaluate("SUBTESTS[1].id")
    session.evaluate(
        f"state.stats.attempts[{st_id!r}]=1; state.stats.correct[{st_id!r}]=1; updateBadges(); true"
    )
    assert session.evaluate(f"getBadge({st_id!r})") is None
