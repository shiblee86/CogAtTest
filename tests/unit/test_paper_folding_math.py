"""Unit tests for the pure geometry math behind the Paper Folding animation:
computeFoldGeometry() picks where the fold lines sit, unfoldPositions()
mirrors a punched hole back out across those lines to find every hole the
unfolded sheet ends up with.
"""
import json

import pytest

pytestmark = pytest.mark.unit


def test_compute_fold_geometry_with_zero_folds_has_no_fold_lines(page):
    session, _ = page
    data = json.loads(session.evaluate("JSON.stringify(computeFoldGeometry(0, 220))"))
    assert data["foldLines"] == []
    assert data["compactTop"] == 0


def test_compute_fold_geometry_places_fold_lines_at_successive_halving_points(page):
    session, _ = page
    data = json.loads(session.evaluate("JSON.stringify(computeFoldGeometry(2, 220))"))
    assert data["foldLines"] == pytest.approx([110, 165])
    assert data["compactTop"] == pytest.approx(165)


@pytest.mark.parametrize("folds", [0, 1, 2, 3, 4])
def test_unfold_positions_count_doubles_with_each_fold(page, folds):
    session, _ = page
    length = session.evaluate(
        f"unfoldPositions(50, computeFoldGeometry({folds}, 220).foldLines).length"
    )
    assert length == 2 ** folds


def test_unfold_positions_mirrors_symmetrically_around_a_single_fold_line(page):
    session, _ = page
    ys = json.loads(session.evaluate("JSON.stringify(unfoldPositions(165, [110]))"))
    assert sorted(ys) == pytest.approx(sorted([165, 55]))


def test_unfold_positions_two_folds_produces_four_evenly_reflected_points(page):
    session, _ = page
    ys = json.loads(session.evaluate("JSON.stringify(unfoldPositions(192.5, [110, 165]))"))
    assert sorted(ys) == pytest.approx(sorted([192.5, 137.5, 82.5, 27.5]))
