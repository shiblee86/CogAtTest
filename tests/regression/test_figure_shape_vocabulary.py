"""Regression tests for the "figures were too elementary" fix: FIGURE_TYPES
grew from 7 shapes to 11 (added octagon, trapezoid, oval, heart), reused by
Figure Analogies, Figure Series (both served by genFigureAnalogyPool()), and
Figure Classification. These tests lock in that the four new shapes are both
present in the data and actually usable by the generators that consume it.
"""
import json

import pytest

pytestmark = pytest.mark.regression

NEW_SHAPES = {"octagon", "trapezoid", "oval", "heart"}
ORIGINAL_SHAPES = {"circle", "square", "triangle", "diamond", "pentagon", "hexagon", "star"}

_STRESS_JS = """
(function(){
  const saved = FIGURE_TYPES.slice();
  FIGURE_TYPES.length = 0;
  FIGURE_TYPES.push('octagon','trapezoid','oval','heart');
  const errors = [];
  let sawEllipse = false, sawHeartPath = false;
  try {
    for (let i=0;i<150;i++) {
      try {
        const q1 = genFigureAnalogyPool();
        const q2 = makeFigureClassification();
        // Concatenate the *raw* (non-JSON-encoded) markup: choices/text hold
        // literal SVG strings with real double quotes. Searching
        // JSON.stringify() output instead would only ever match escaped
        // backslash-quote sequences and silently never fire.
        const blob = [q1.text, ...(q1.choices || [])].join('')
                   + [q2.text, ...(q2.choices || [])].join('');
        if (blob.includes('<ellipse')) sawEllipse = true;
        if (/<path d="M [^"]*C [^"]*C /.test(blob)) sawHeartPath = true;
      } catch(e) { errors.push(String(e && e.message || e)); }
    }
  } finally {
    FIGURE_TYPES.length = 0;
    FIGURE_TYPES.push(...saved);
  }
  const restored = JSON.stringify(FIGURE_TYPES.slice().sort()) === JSON.stringify(saved.slice().sort());
  return JSON.stringify({errors, sawEllipse, sawHeartPath, restored});
})()
"""


def test_figure_types_is_exactly_the_original_seven_plus_the_four_new_shapes(page):
    session, _ = page
    figure_types = set(json.loads(session.evaluate("JSON.stringify(FIGURE_TYPES)")))
    assert figure_types == ORIGINAL_SHAPES | NEW_SHAPES


def test_figure_generators_survive_stress_when_restricted_to_only_the_new_shapes(page):
    """Restricts FIGURE_TYPES (in this tab only) to exactly the four newest
    shapes and hammers the generators that read from it. Existing rules that
    build "wrong" choices via FIGURE_TYPES.filter(...)/shuffle(...).slice(...)
    are exactly the kind of code a smaller or differently-shaped pool could
    break (e.g. producing a duplicate choice, which validateQuestion() would
    reject) -- restricting to only the new shapes is a strictly harder case
    than the shipped 11-shape pool, so it's a stronger guarantee than just
    stress-testing the generators unchanged.
    """
    session, _ = page
    data = json.loads(session.evaluate(_STRESS_JS))
    assert not data["errors"], f"figure generators broke with an all-new-shape pool: {data['errors']}"
    assert data["sawEllipse"], "oval (<ellipse>) never appeared across 150 draws"
    assert data["sawHeartPath"], "heart (cubic-bezier <path>) never appeared across 150 draws"
    assert data["restored"], "FIGURE_TYPES was not restored to its original 11 shapes after the test"
