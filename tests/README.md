# Test suite

CogAtTest is a vanilla HTML/CSS/JS app with no build step and no Node
toolchain in this repo. Rather than a JS test runner (Jest/Vitest), this
suite drives the real app inside real headless Chrome via the Chrome
DevTools Protocol, and asserts on live JS state / the live DOM, from plain
`pytest`.

## Setup

```
pip install -r requirements-test.txt
```

Requires a `google-chrome` / `chromium` binary on PATH, and Python 3's
`http.server` (stdlib) to serve the app.

## Running

```
pytest                    # everything
pytest -m unit             # only unit tests (fast, no UI interaction)
pytest -m integration      # only end-to-end UI flows
pytest -m regression       # only "must not break again" tests
pytest -k shape             # anything shape-related, any suite
pytest -x -q                # stop on first failure, quiet
```

## Layout

- `tests/unit/` -- individual functions in isolation (svgFigure(), pick(),
  shuffle(), computeFoldGeometry(), getAccuracy(), validateQuestion(), ...).
  No clicking; just calling functions in the loaded page and checking
  return values.
- `tests/integration/` -- real UI flows: open a subtest, click Quiz, click
  through every question, check results/mastery/localStorage. Theme toggle
  and its persistence. Mistake recording and the Review flow.
- `tests/regression/` -- locks in the two most recent feature deliverables
  so they can't silently regress: the figure-shape vocabulary expansion
  (7 -> 11 shapes) and the card-artwork wiring (PHOTO_CARDS/CSS/assets), plus
  a stress test across *every* subtest's generator and the pre-existing
  (non-FIGURE_TYPES) svgFigure() shape branches, to catch collateral damage
  from a change that was only supposed to touch figures/cards.

## How it works

- `tests/cdp.py` -- a small synchronous wrapper around a Chrome DevTools
  Protocol websocket connection (`Runtime.evaluate`, `Page.navigate`,
  clicking, screenshots).
- `tests/conftest.py` -- starts one static file server and one headless
  Chrome for the whole test session (fast), but gives every test function
  its own browser tab with `localStorage` cleared and the app reloaded
  (isolated) via the `page` fixture.
- `tests/helpers.py` -- shared helpers for tests that need to click through
  an actual quiz session (answer the current question correctly/incorrectly
  by finding the matching rendered choice button, same comparison
  `handleAnswer()` itself uses).
