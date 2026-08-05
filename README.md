# CogAT Detective Academy

A free, browser-based practice app for the COGAT® Level 8 test, styled as a
kid-friendly "detective academy." Every question is generated fresh in the
browser — no two attempts are ever the same — across all three COGAT®
batteries plus a bonus Logic Games subtest.

If GitHub Pages is enabled for this repo, it's served at
`https://shiblee86.github.io/CogAtTest/`.

## Features

- **13 COGAT® subtests** across Verbal, Quantitative, and Nonverbal
  batteries, plus a Logic Games bonus subtest (Mini Sudoku) — Picture &
  Figure Analogies, Sentence Completion, Picture & Figure Classification,
  Paper Folding, Number Analogies/Series/Puzzles, Abacus Series, Divided /
  Nested / Rotating Shapes.
- **Unlimited, procedurally generated questions** — nothing is pulled from a
  fixed bank, so Quiz/Exam/Test Mode never repeat the same question twice.
- **Quiz, Exam, and timed Test Mode** per subtest, with mastery badges
  (bronze/silver/gold), a daily mission, and a mistake-review flow.
- **Audio-first Sentence Completion** (real speech synthesis, text hidden by
  default) matching the test's listening-comprehension format.
- **Light/dark theme**, keyboard-navigable cards, reduced-motion support.
- **Everything runs client-side.** No account, no server — progress is
  saved to `localStorage` on your own device.

## Running it locally

No build step, no dependencies. Any static file server works:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/index.html
```

Opening `index.html` directly (`file://`) also works, though a local server
avoids any browser restrictions on `file://` resource loading.

## Project structure

```
index.html      Page skeleton — header, home/detail view containers
app.js          The entire app: state, question generators, SVG rendering,
                session engine, view rendering (see DESIGN.md)
styles.css      All styling and theme variables
assets/         Card illustration images + page background
tests/          pytest test suite (unit / integration / regression) — see
                tests/README.md
```

See [`DESIGN.md`](DESIGN.md) for the full architecture writeup (state
model, the question-generator contract, the SVG rendering engine, session
flow, and known trade-offs).

## Testing

```bash
pip install -r requirements-test.txt
pytest
```

The suite drives the real app in headless Chrome (there's no Node
toolchain in this repo) and is split into `unit`, `integration`, and
`regression` markers — see [`tests/README.md`](tests/README.md) for
details and filtering examples.

## For parents

The app includes an in-app "For Parents" guide (test format, scoring,
test-day tips) accessible from the header. As it notes there: practice
accuracy in this app cannot be translated into an actual test percentile —
it's meant to build familiarity and confidence, not predict a score.
