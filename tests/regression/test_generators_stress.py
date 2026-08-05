"""Regression guard: every subtest's question generator must keep producing
well-formed questions (validateQuestion() must not throw) under repeated
random generation. This is the broad safety net for "no other question type
broke" -- paper folding, number series/puzzles, sudoku, abacus, picture
analogies etc. are all included, not just the figure-based ones the shape
vocabulary change touched directly.
"""
import json

import pytest

pytestmark = pytest.mark.regression

ITERATIONS = 150

_STRESS_ALL_JS = f"""
(function(){{
  const results = {{}};
  for (const st of SUBTESTS) {{
    const errors = [];
    for (let i=0;i<{ITERATIONS};i++) {{
      try {{ st.gen(); }} catch(e) {{ errors.push(String(e && e.message || e)); }}
    }}
    results[st.id] = errors;
  }}
  return JSON.stringify(results);
}})()
"""


def test_every_subtest_generator_produces_valid_questions_under_stress(page):
    session, _ = page
    results = json.loads(session.evaluate(_STRESS_ALL_JS))
    failing = {k: v for k, v in results.items() if v}
    assert not failing, f"generators threw during {ITERATIONS} stress iterations: {failing}"
    assert set(results.keys()) == set(
        json.loads(session.evaluate("JSON.stringify(SUBTESTS.map(s => s.id))"))
    )


@pytest.mark.parametrize(
    "subtest_id",
    [
        "paper-folding",
        "num-series",
        "num-puzzles",
        "num-analogies",
        "abacus-series",
        "sudoku",
        "pic-analogies",
        "pic-classification",
        "sentence-comp",
    ],
)
def test_non_figure_subtests_are_unaffected_by_the_shape_vocabulary_change(page, subtest_id):
    """These subtests don't read FIGURE_TYPES at all, so a change scoped to
    svgFigure()/FIGURE_TYPES/PHOTO_CARDS should never be able to break them.
    Generating and validating a batch here is a targeted tripwire in case a
    future edit accidentally widens its blast radius.
    """
    session, _ = page
    errors = json.loads(session.evaluate(
        f"""
        JSON.stringify((function(){{
          const st = SUBTESTS.find(s => s.id === {subtest_id!r});
          const errors = [];
          for (let i=0;i<{ITERATIONS};i++) {{
            try {{ st.gen(); }} catch(e) {{ errors.push(String(e && e.message || e)); }}
          }}
          return errors;
        }})())
        """
    ))
    assert not errors, f"{subtest_id} generator threw: {errors}"
