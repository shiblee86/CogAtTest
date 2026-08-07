"""The most basic possible guarantee for the Android wrapper: the project
still builds. Everything else in this suite depends on debug_apk succeeding
first (it's a session-scoped fixture, so this doesn't build twice).
"""
import pytest

pytestmark = pytest.mark.android


def test_assemble_debug_produces_a_non_empty_apk(debug_apk):
    assert debug_apk.exists()
    assert debug_apk.stat().st_size > 0
