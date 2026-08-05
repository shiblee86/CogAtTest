"""Unit tests for the small pure-ish helper functions in app.js.

Each of these is exercised directly (no clicking, no navigation beyond the
initial page load) to isolate its own logic from the rest of the app.
"""
import json

import pytest

pytestmark = pytest.mark.unit


def test_pick_only_returns_elements_from_the_input_array(page):
    session, _ = page
    values = json.loads(session.evaluate(
        "JSON.stringify(Array.from({length:50}, () => pick(['a','b','c'])))"
    ))
    assert len(values) == 50
    assert set(values) <= {"a", "b", "c"}
    # Not a hardcoded first-element return -- pick() should vary over 50 draws.
    assert len(set(values)) > 1


def test_shuffle_returns_a_permutation_without_mutating_its_input(page):
    session, _ = page
    data = json.loads(session.evaluate(
        """
        (function(){
          const original = [1,2,3,4,5];
          const copy = [...original];
          const shuffled = shuffle(copy);
          return JSON.stringify({
            inputUnchanged: JSON.stringify(copy) === JSON.stringify(original),
            sameLength: shuffled.length === original.length,
            sameMultiset: JSON.stringify([...shuffled].sort()) === JSON.stringify([...original].sort()),
          });
        })()
        """
    ))
    assert data["inputUnchanged"] is True
    assert data["sameLength"] is True
    assert data["sameMultiset"] is True


def test_uniq_removes_duplicates_preserving_first_occurrence_order(page):
    session, _ = page
    result = json.loads(session.evaluate("JSON.stringify(uniq([1,2,2,3,1,4]))"))
    assert result == [1, 2, 3, 4]


def test_ensure_four_pads_a_short_list_to_exactly_four_unique_values(page):
    session, _ = page
    result = json.loads(session.evaluate("JSON.stringify(ensureFour(['x'], 'filler'))"))
    assert len(result) == 4
    assert len(set(result)) == 4
    assert "x" in result


def test_ensure_four_still_reaches_four_unique_values_from_all_duplicates(page):
    session, _ = page
    result = json.loads(session.evaluate("JSON.stringify(ensureFour(['a','a','a','a'], 'f'))"))
    assert len(result) == 4
    assert len(set(result)) == 4


def test_generate_question_id_is_deterministic_and_content_sensitive(page):
    session, _ = page
    id1, id2, id3 = json.loads(session.evaluate(
        """
        JSON.stringify([
          generateQuestionId({a:1,b:'x'}),
          generateQuestionId({a:1,b:'x'}),
          generateQuestionId({a:2,b:'x'}),
        ])
        """
    ))
    assert id1 == id2, "same content must hash to the same id"
    assert id1 != id3, "different content must hash to a different id"
    assert id1.startswith("q_")


def test_shuffle_bag_exhausts_every_index_exactly_once_per_cycle(page):
    session, _ = page
    first_cycle = json.loads(session.evaluate(
        """
        (function(){
          const next = createShuffleBag(5);
          return JSON.stringify(Array.from({length:5}, next).sort((a,b)=>a-b));
        })()
        """
    ))
    assert first_cycle == [0, 1, 2, 3, 4]


def test_shuffle_bag_never_repeats_the_same_index_back_to_back_across_cycles(page):
    session, _ = page
    has_adjacent_repeat = session.evaluate(
        """
        (function(){
          const next = createShuffleBag(3);
          const draws = Array.from({length:300}, next);
          for (let i=1;i<draws.length;i++) if (draws[i]===draws[i-1]) return true;
          return false;
        })()
        """
    )
    assert has_adjacent_repeat is False
