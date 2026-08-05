# CogAT Detective Academy — Design Document

## 1. What this is

A single-page, client-only web app that generates unlimited practice
questions for the COGAT® Level 8 test (Verbal, Quantitative, Nonverbal
batteries, plus a Logic Games bonus subtest), styled as a "detective
academy" game for a young child. There is no backend, no build step, and no
account system — every question is generated on the fly in the browser and
progress lives in `localStorage` on the child's own device.

**Files:**

| File | Role |
|---|---|
| `index.html` | ~35-line skeleton: header, two view containers (`#homeView`, `#detailView`), script tags. Everything else is rendered by JS. |
| `app.js` | The entire application — state, question generators, SVG rendering, session engine, view rendering. ~2,200 lines, one file, no imports. |
| `styles.css` | All styling, theme variables, responsive rules. |
| `assets/` | Card-illustration PNGs and the page-background mascot image. |
| `tests/` | pytest + headless-Chrome test suite (see `tests/README.md`). |

## 2. Why this shape (constraints that drove the design)

- **Static hosting only** (GitHub Pages). No server means no build pipeline
  is required either — the repo ships exactly what the browser runs.
- **A young child is the end user.** This pushes several decisions: audio
  read-aloud for Sentence Completion, full-color Twemoji pictures instead of
  relying on the OS's emoji font, large tap targets, `prefers-reduced-motion`
  handling, a light/dark theme toggle.
- **No two attempts should look the same.** Nearly everything is
  procedurally generated per-question rather than pulled from a fixed bank,
  which is why the question-generator contract (§5) exists at all — with a
  fixed question bank you wouldn't need a runtime validator.
- **No TypeScript, no framework, no test runner in the toolchain.** The app
  intentionally has zero dependencies at runtime (`twemoji` is the one
  exception, loaded from a CDN with a graceful fallback if it's unreachable).
  This shows up throughout the design: contracts are enforced by a runtime
  validator (§5) rather than a type system, and the test suite drives a real
  browser via CDP instead of a JS test runner (§9), because there's no Node
  toolchain to run one in.

## 3. Script architecture

`app.js` is **not wrapped in an IIFE** — every top-level `const`/`function`
declaration is a script-scope global (`FIGURE_TYPES`, `SUBTESTS`,
`svgFigure`, `state`, `session`, etc. are all directly accessible). The file
is organized into banner-commented sections that act as informal modules:

```
STATE & STORAGE  →  HELPERS  →  QUESTION ID GENERATOR  →  VALIDATION
→  SVG ENGINE  →  PAPER FOLDING  →  ABACUS  →  ICON SYSTEM
→  QUESTION GENERATORS (one per subtest)  →  SUBTEST DEFINITIONS
→  MISTAKE TRACKING  →  RENDER ENGINE  →  SESSION ENGINE  →  INIT
```

This is a deliberate trade-off: no module boundaries or build step to
maintain, at the cost of no real encapsulation — anything can reach into
`state` or call any generator directly. In practice this is what makes the
CDP-based test suite possible at all (tests call `svgFigure()`,
`SUBTESTS`, `validateQuestion()` etc. directly in the live page), but it
also means naming collisions are avoided purely by convention, not by the
language.

Execution starts at `document.addEventListener('DOMContentLoaded', ...)`
near the bottom of the file (§8), **not** at the top of the script — a few
top-level statements do run immediately at parse time (e.g.
`document.getElementById('totalSubtests').innerText = SUBTESTS.length`
right after `SUBTESTS` is defined), but the actual UI (`renderHome()`)
only appears once `DOMContentLoaded` fires.

## 4. State model

```js
let state = {
  mastery: {},                                   // { [subtestId]: {earned, score, total, earnedAt} }
  stats: { attempts: {}, correct: {}, wrong: {} }, // each: { [subtestId]: count }
  badges: [],                                     // [{ id: subtestId, level: 'bronze'|'silver'|'gold' }]
  mistakes: [],                                   // [{ subtestId, question: JSON string, selected, correct, timestamp }]
  dailyMission: null,                              // { date, subtestIds: [3 ids], completed: {} }
  session: null,                                   // declared but not actually wired up (see note below)
};
```

- Persisted as one JSON blob under `localStorage['cogat_precision_v5']`
  (`loadState()` / `saveState()`). The version suffix in the key is the
  migration strategy: an incompatible state shape gets a new key rather than
  an in-place migration, and `loadState()` merges onto the default shape
  with a shallow spread so old saves missing newer fields don't crash.
- `state.dailyMission` regenerates once per calendar day (`date` compared
  against `today`), picking 3 random subtest ids via `shuffle()`.
- **Note:** `state.session` is initialized but never read or written
  anywhere else in the file. The actual in-progress quiz/exam/test session
  lives in a separate top-level `session` variable (§7) that is
  intentionally *not* persisted — refreshing mid-quiz loses that quiz, by
  design (there's no "resume" feature). Existing consumers should not treat
  `state.session` as meaningful.
- Two more small keys live outside the main blob: `cogat_theme`
  (`'dark'`/`'light'`) and `cogat_showSentenceText` (`'1'`/`'0'`), read once
  at startup and written on their respective toggles.

## 5. The subtest system

`SUBTESTS` (one array, ~14 entries) is the single source of truth for the
whole app — the home screen, the study guide, the quiz/exam flow, and the
mastery header count are all *derived* from it rather than hardcoded per
subtest:

```js
{ id, name, battery, icon, desc, quizN, examN, gen, tipTitle, tip, example, testTips }
```

- `id` — kebab-case, used as `data-id` on cards, as the `localStorage`
  mistake/stats/mastery key, and as the CSS selector hook for card artwork.
- `battery` — one of 4 literal strings (`'Verbal 🗣️'`, `'Nonverbal 🔷'`,
  `'Quantitative 🔢'`, `'Logic Games 🧩'`); `renderHome()` groups cards by
  filtering `SUBTESTS` on this string, so it's a soft grouping key, not a
  separate battery entity.
- `gen` — a zero-argument function reference (§6) that produces one
  question. `quizN`/`examN` are how many `gen()` calls a Quiz vs. an Exam
  session makes (§7).

Adding a new subtest is meant to be as close to "add one object to this
array + write its `gen` function" as the architecture gets — nothing else
needs to know it exists. The one exception is `PHOTO_CARDS` (§8), a
separate `Set` of ids that currently mirrors `SUBTESTS` 1:1; a new subtest
without matching entries there falls back to a plain icon-watermark card
instead of an illustration.

## 6. Question-generator contract

Every subtest's `gen()` (e.g. `makeNumberSeries`, `makeSudoku`,
`genFigureAnalogyPool`) is a zero-argument function that builds a question
object and pipes it through two shared functions before returning:

```js
q.id = generateQuestionId(q);       // content hash -> stable id for identical content
return validateQuestion(q, subtestId);
```

`validateQuestion()` is the actual contract enforcement, since there's no
type system to do it at compile time:

- `q.correct` must be set.
- `q.choices` must have **exactly 4** entries.
- Choices must be **4 unique values** (string equality, or `.text` for
  object-shaped picture choices) — this is the check that made the recent
  figure-shape vocabulary expansion risky enough to need a stress-test
  regression suite (a smaller/differently-shaped shape pool could produce a
  duplicate "wrong" choice).
- `q.correct` must actually appear among `q.choices`.
- `q.explanation` and `q.steps` (≥2 entries, used by the "show step-by-step"
  tutor) must be present.

Field-wise, every question shares `{choices, correct, explanation, steps,
id}`; the "what does the user see" fields vary by `q.type` and are
interpreted by `renderQuestion()` (§7): `text` (default/figure types),
`qText` + `svgHTML` (paper folding), `sentence` (sentence completion, read
aloud rather than shown). `safeGenerate()` wraps every `gen()` call in
try/catch in production so one broken generator produces "skip and try
again" instead of locking the whole quiz — the test suite's stress tests
(§9) exist specifically to make that catch block stay empty in practice.

`serializeQuestion()` is a second, narrower contract: it's the subset of a
question's fields worth persisting into `state.mistakes` for the Review
flow (drops nothing structurally interesting, but is a separate allowlist
from `validateQuestion`'s requirements, so a field added to one won't
automatically show up in the other).

## 7. Rendering flow and the session engine

There is no router and no framework — `renderX()` functions build an HTML
string and assign it to `.innerHTML`, then imperatively wire up
`.onclick`/`addEventListener` on the fresh nodes. Two containers toggle
visibility via a `.hidden` class:

```
renderHome()  ⇄  openSubtest(id) → renderStudy()  →  startSession(mode) → renderQuestion() (loop) → finishSession()
```

- **Home** (`renderHome`) — groups `SUBTESTS` by battery, renders one card
  per subtest via `renderCard()`, renders the daily mission, updates the
  mastered-count header.
- **Study** (`renderStudy`) — one subtest's tip/example/stats plus
  Quiz/Exam/Test Mode/Review buttons (Review only appears if
  `getMistakesForSubtest(id).length > 0`).
- **Session** (`startSession(mode)`) — builds a `questions` array by calling
  `gen()` (deduped by `q.id` via a `Set`) `quizN` or `examN` times for
  `'quiz'`/`'exam'`/`'test'`, or by restoring previously-missed questions
  from `state.mistakes` for `'review'`. Stores everything in one
  module-level `session` object:

  ```js
  session = { mode, questions, idx: 0, score: 0, answers: [], locked, subtestId, timerId };
  ```

- **Question loop** (`renderQuestion` → `handleAnswer` → `advanceSession`) —
  `handleAnswer()` compares the clicked choice's value against `q.correct`
  (string equality, with a couple of type-shape special cases for
  object-shaped and inline-SVG-string choices), updates `state.stats`,
  records a mistake or resolves one (in review mode), updates badges, saves
  state, then reveals correct/wrong styling on every choice button — except
  in `'test'` mode, where nothing is revealed until `finishSession()`
  (mirrors real proctored-test conditions).
- **Finish** (`finishSession`) — Quiz/Exam: ≥80% is a pass, ≥95% shows a
  "Gifted Ready" badge; an Exam pass writes `state.mastery[id]` and fires
  confetti. Test mode routes to `renderTestResults()` instead, which is the
  only place a Test-mode child sees right/wrong per-question feedback.

`updateBadges()` recomputes all badges from `state.stats` on every answer
(gold: ≥90% accuracy & ≥5 attempts; silver: ≥70% & ≥3; bronze: ≥50% & ≥2) —
badges are a derived view over `stats`, not something incrementally
updated, so they self-correct if `stats` ever changes by another path.

## 8. SVG rendering engine

Everything visual in a question (other than verbal-content pictures, see
below) is generated SVG, not image assets — this is what makes "no two
attempts look the same" affordable.

- **`svgFigure(type, opts)`** — one function, one big `if/else if` chain
  keyed on shape name, shared by every figure-based subtest. Draws basic
  shapes (`circle`, `square`, `triangle`, `diamond`, `pentagon`, `hexagon`,
  `octagon`, `trapezoid`, `oval`, `star`, `heart` — the last four added in a
  recent expansion from an original set of 7), directional/asymmetric
  shapes (`arrow-*`, `flag`, `lshape`), composite shapes (`nested`,
  `divided-*`, `half-shaded-*`, `with-lines`, `with-diagonal`, `dot-grid`),
  plus generic overlay options (`fill: 'dots'|'stripes'|'checker'` via a
  `<pattern>` in `<defs>`, `rotation`, `scale`, `reflect`, `dashed`,
  `divided`). `FIGURE_TYPES` is the pickable pool most figure generators
  draw from via `pick()`/`shuffle()`; a handful of classification rules use
  hardcoded literal shape names instead (e.g. "all have 4 sides" always
  uses `square`/`diamond`), so not every shape a child sees necessarily came
  from `FIGURE_TYPES`.
- **`paperFoldingSVG()` / `computeFoldGeometry()` / `unfoldPositions()`** —
  pure geometry for the fold animation: fold lines are placed at successive
  halving points of the sheet height, and a punched hole's final positions
  are found by mirroring it across each fold line from the last fold back
  to the first (`2^folds` positions per punch). `playFoldAnimation()` /
  `playUnfoldAnimation()` drive the actual CSS-transitioned fold/unfold.
- **`abacusSVG()`** — draws rods + beads for Abacus Series questions.
- **Two separate icon systems, for two different jobs:**
  - `getIconPath(name, size)` — a hand-authored `ICON_REGISTRY` of ~100
    monochrome line-art SVG paths (`stroke: var(--text)`), used for
    decorative/UI icons.
  - `iconSVG(name, size)` — an `EMOJI_MAP` of real emoji glyphs, rendered as
    full-color Twemoji `<img>` tags (CDN, with an `onerror` fallback to the
    native glyph). Used specifically where the picture itself *is* the
    answer choice (Picture Analogies/Classification/Sentence Completion) —
    native OS emoji fonts are inconsistent (some render monochrome), so
    Twemoji guarantees every child sees the identical crisp picture.

## 9. Card artwork subsystem

Added after two rounds of customer feedback (figures "too elementary", home
cards needed illustration instead of plain icon watermarks):

- `PHOTO_CARDS` (a `Set` of subtest ids, app.js) → `renderCard()` adds a
  `has-photo` class to the card button when its id is in the set.
- `styles.css` has one `.subtest-card[data-id="..."].has-photo` rule per id,
  each pairing a dark scrim `linear-gradient` with a `url('assets/grid-*.png')`
  background-image — the gradient exists purely for text legibility, since
  the app's default text color is dark in light mode and would be unreadable
  directly on a photo.
- `#bgMotif` is a fixed, `z-index: -1`, low-opacity (`0.16`) full-page
  background layer (the samurai mascot) — negative z-index specifically so
  it paints behind ordinary non-positioned content instead of on top of it.

## 10. Theming

CSS custom properties on `:root` define the light palette; `body.dark`
overrides them for dark mode (no separate dark stylesheet). `toggleTheme()`
flips a `dark` boolean, calls `applyTheme()` (toggles the `body.dark` class,
updates the theme button's label/`aria-pressed`), and persists the choice to
`localStorage['cogat_theme']`, read back on the next load before first
paint of `renderHome()`.

## 11. Accessibility & UX details worth knowing

- `#liveRegion` (`aria-live="polite"`) + `announce(msg)` narrate view
  changes and answer feedback for screen readers.
- `focusEl(selector)` moves keyboard focus to the newly relevant element
  after each render (e.g. the first choice button, the exit button).
- Cards are `<button>` elements with `keydown` handling for Enter/Space, not
  just click — keyboard-only navigation works without extra ARIA.
- `@media (prefers-reduced-motion: reduce)` collapses all animations
  (confetti included) to effectively instant.
- Sentence Completion is audio-first by design: the question is spoken via
  `speechSynthesis` automatically, text is hidden by default
  (`showSentenceText`, opt-in and persisted) — mirrors the real test's
  listening-comprehension format for children who may not read fluently yet.

## 12. Testing

See `tests/README.md`. In short: no Node toolchain exists in this repo, so
the suite (`unit`/`integration`/`regression`, pytest-marker-separated)
drives the real app inside headless Chrome via a small CDP client and
asserts on live JS state and the live DOM, rather than using a JS test
runner. The regression suite in particular exists to encode "this specific
past change must not silently break again" — most usefully, a stress test
that hammers every `SUBTESTS[].gen()` (and, restricted to only the newest
shapes, the figure generators specifically) hundreds of times per run,
because `validateQuestion()`'s duplicate-choice check is exactly the kind
of failure a bad shape pool would only trigger occasionally in production.

## 13. Known trade-offs / non-goals

- **No offline/PWA support** beyond what the browser does automatically —
  no service worker, no manifest. A GitHub Pages static host is the only
  deployment target considered.
- **No accounts, no cross-device sync.** Progress is tied to one browser's
  `localStorage`; clearing site data or switching devices loses it.
  Acceptable for a single-child household tool, not for a multi-user product.
- **No percentile/stanine scoring.** The app is explicit in its own copy
  (`renderParentsGuide`) that practice-question accuracy cannot be
  translated into an actual test percentile — it deliberately avoids
  implying it can.
- **Runtime-enforced contracts, not compile-time ones.** Any future
  generator bug shows up as a thrown error caught by `safeGenerate()` (a
  skipped question) or, if `validateQuestion` itself is bypassed, as a
  malformed question reaching the UI. There's no static type checking
  anywhere in the file.
