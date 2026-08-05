"""Shared helpers for integration/regression tests that need to click through
a real quiz session rather than call internal functions directly.
"""

# Clicks whichever rendered choice button's dataset.value matches the current
# question's correct answer -- the same comparison handleAnswer() itself uses
# (app.js:1965-1968), so this exercises the real click -> handleAnswer() path.
_CLICK_CORRECT_JS = """
(function(){
  const q = session.questions[session.idx];
  const correctValue = (typeof q.correct === 'object' && q.correct.text) ? q.correct.text : q.correct;
  const btns = Array.from(document.querySelectorAll('#choicesGrid .choice-btn'));
  const target = btns.find(b => b.dataset.value === correctValue);
  if (!target) return false;
  target.click();
  return true;
})()
"""

_CLICK_WRONG_JS = """
(function(){
  const q = session.questions[session.idx];
  const correctValue = (typeof q.correct === 'object' && q.correct.text) ? q.correct.text : q.correct;
  const btns = Array.from(document.querySelectorAll('#choicesGrid .choice-btn'));
  const target = btns.find(b => b.dataset.value !== correctValue);
  if (!target) return false;
  target.click();
  return true;
})()
"""


def answer_correctly(session):
    assert session.evaluate(_CLICK_CORRECT_JS), "no choice button matched the correct answer"


def answer_wrong(session):
    assert session.evaluate(_CLICK_WRONG_JS), "no incorrect choice button was found"


def open_subtest_and_start(session, index, mode_button_id):
    """Opens SUBTESTS[index]'s study guide from the home screen and starts a
    session via the given mode button (#quizBtn / #examBtn / #testModeBtn).
    Returns the subtest id.
    """
    st_id = session.evaluate(f"SUBTESTS[{index}].id")
    session.click(f'.subtest-card[data-id="{st_id}"]')
    session.click(f"#{mode_button_id}")
    return st_id
