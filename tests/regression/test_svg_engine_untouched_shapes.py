"""Regression guard for svgFigure()'s pre-existing, non-FIGURE_TYPES shape
branches (arrow-*, divided-*, half-shaded-*, with-lines, with-diagonal,
dot-grid, flag, lshape) -- these were explicitly called out as untouched
when octagon/trapezoid/oval/heart were added right above them in the same
if/else if chain. A future edit to that shared chain (e.g. inserting a new
`else if` in the wrong place) could silently break one of these without
touching FIGURE_TYPES at all, which the figure-vocabulary regression tests
would not catch.
"""
import pytest

pytestmark = pytest.mark.regression

UNTOUCHED_SHAPES = [
    "arrow-up", "arrow-down", "arrow-left", "arrow-right",
    "divided-square", "divided-circle",
    "half-shaded-square", "half-shaded-circle",
    "with-lines", "with-diagonal", "dot-grid",
    "flag", "lshape",
]


@pytest.mark.parametrize("shape", UNTOUCHED_SHAPES)
def test_untouched_shape_still_renders_valid_svg(page, shape):
    session, _ = page
    svg = session.evaluate(f"svgFigure({shape!r}, {{size:60, stroke:'#000'}})")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "undefined" not in svg
    assert "NaN" not in svg


@pytest.mark.parametrize("shape,min_elements", [
    ("divided-square", 2),   # rect + bisecting line
    ("divided-circle", 2),   # circle + bisecting line
    ("with-lines", 3),       # rect + horizontal line + vertical line
    ("with-diagonal", 2),    # rect + diagonal line
    ("flag", 2),             # pole line + flag polygon
])
def test_untouched_composite_shape_keeps_all_of_its_sub_elements(page, shape, min_elements):
    session, _ = page
    svg = session.evaluate(f"svgFigure({shape!r}, {{size:60, stroke:'#000'}})")
    element_count = sum(svg.count(f"<{tag}") for tag in ("rect", "circle", "line", "polygon", "path", "ellipse"))
    assert element_count >= min_elements, svg
