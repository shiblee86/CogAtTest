"""Unit tests for svgFigure() -- the SVG shape engine behind Figure Analogies,
Figure Classification, Figure Series, and Nested/Divided/Rotating Shapes.
"""
import json

import pytest

pytestmark = pytest.mark.unit

# Root SVG element each shape type is expected to draw. Used both to sanity
# check well-known shapes and to confirm each of the four newest shapes
# (octagon, trapezoid, oval, heart) draws the element type its geometry implies.
SHAPE_ROOT_TAG = {
    "circle": "<circle",
    "square": "<rect",
    "triangle": "<polygon",
    "diamond": "<polygon",
    "pentagon": "<polygon",
    "hexagon": "<polygon",
    "star": "<polygon",
    "octagon": "<polygon",
    "trapezoid": "<polygon",
    "oval": "<ellipse",
    "heart": "<path",
}


@pytest.mark.parametrize("shape,root_tag", sorted(SHAPE_ROOT_TAG.items()))
def test_svg_figure_renders_expected_root_element_with_no_broken_interpolation(page, shape, root_tag):
    session, _ = page
    svg = session.evaluate(f"svgFigure({json.dumps(shape)}, {{size:60, stroke:'#000'}})")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert root_tag in svg
    assert "undefined" not in svg
    assert "NaN" not in svg


def test_figure_types_lists_exactly_the_eleven_expected_shapes(page):
    session, _ = page
    figure_types = json.loads(session.evaluate("JSON.stringify(FIGURE_TYPES)"))
    assert len(figure_types) == 11
    assert set(figure_types) == set(SHAPE_ROOT_TAG.keys())


@pytest.mark.parametrize("fill_kind", ["dots", "stripes", "checker"])
def test_svg_figure_pattern_fills_emit_a_defs_pattern_and_reference_it(page, fill_kind):
    session, _ = page
    svg = session.evaluate(f"svgFigure('circle', {{size:60, stroke:'#000', fill:{json.dumps(fill_kind)}}})")
    assert "<defs>" in svg
    assert "<pattern" in svg
    assert f'fill="url(#pat_{fill_kind}_' in svg


def test_svg_figure_rotation_option_wraps_markup_in_a_rotate_transform(page):
    session, _ = page
    svg = session.evaluate("svgFigure('square', {size:60, stroke:'#000', rotation:45})")
    assert "rotate(45," in svg


def test_svg_figure_dashed_option_adds_stroke_dasharray(page):
    session, _ = page
    plain = session.evaluate("svgFigure('circle', {size:60, stroke:'#000'})")
    dashed = session.evaluate("svgFigure('circle', {size:60, stroke:'#000', dashed:true})")
    assert "stroke-dasharray" not in plain
    assert "stroke-dasharray" in dashed


def test_svg_figure_divided_option_adds_a_bisecting_line_to_any_shape(page):
    session, _ = page
    svg = session.evaluate("svgFigure('heart', {size:60, stroke:'#000', divided:true})")
    assert svg.count("<line") == 1


def test_nested_shape_composes_an_outer_and_inner_base_shape(page):
    session, _ = page
    svg = session.evaluate(
        "svgFigure('nested', {size:60, stroke:'#000', outer:'circle', inner:'square'})"
    )
    assert "<circle" in svg
    assert "<rect" in svg


def test_svg_figure_size_option_controls_the_viewbox(page):
    session, _ = page
    svg = session.evaluate("svgFigure('circle', {size:44, stroke:'#000'})")
    assert 'viewBox="0 0 44 44"' in svg
