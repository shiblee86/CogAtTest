# Android wrapper

A thin native shell around the existing web app: one Activity, one WebView,
loading `file:///android_asset/index.html`. All state, question generation,
and rendering logic still lives entirely in `app.js` — nothing was
reimplemented natively.

## How it's kept in sync with the web app

The Android build does **not** read `index.html`/`app.js`/`styles.css`/
`assets/` from the repo root — it only sees whatever was last copied into
`app/src/main/assets/`. After changing anything in the web app, re-sync
before rebuilding:

```bash
./sync-assets.sh
```

## Building

Requires a JDK (17 or 21) and the Android SDK (`platforms;android-34`,
`build-tools;34.0.0`) on your machine. Point `local.properties` at your SDK
(not committed — machine-specific):

```bash
echo "sdk.dir=$ANDROID_HOME" > local.properties
./gradlew assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`.

## Automated tests

`tests/android/` (run via `pytest -m android` from the repo root) covers:
the build actually succeeding, the built APK's manifest (package name,
launcher activity, permissions, min SDK) via `aapt dump badging`, the
bundled web assets being byte-identical to the repo root (catches a
forgotten `sync-assets.sh`), and the built APK's asset tree containing
everything `MainActivity` expects. It skips cleanly (not fails) on a
machine without a JDK/Android SDK. See `tests/README.md`.

**What it does not do: launch the app.** There's no emulator/device in
scope for those tests, so a real device pass is still the only way to
verify the items below.

## Installing / running

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Or open this `android/` directory directly in Android Studio and run from
there (it's a standard Gradle project, no special import steps).

Before treating this as done, do a real install-and-click-through pass and
confirm:
- Progress (mastery/stats/mistakes) survives an app restart (exercises
  `domStorageEnabled`/localStorage under `file://`).
- Sentence Completion's "Read Aloud" actually speaks (exercises
  `window.speechSynthesis` through `WebChromeClient`, which depends on the
  device having a TTS engine/voice installed).
- Rotating the device mid-quiz doesn't lose progress (exercises the
  `android:configChanges` handling in the manifest).

## Known trade-off: APK size

The debug APK is **~97MB**, almost entirely the card-artwork PNGs bundled
under `assets/assets/` (several are 5–9MB each for what renders as a small
card thumbnail on screen). That's fine for a website (loaded once, cached
by the browser) but heavy for an app users download in full. If this is
going anywhere beyond side-loading (e.g. the Play Store), re-compressing/
down-scaling those source PNGs in the web app itself (they'd help page-load
time there too) would be worth doing before shipping — that wasn't done
here since it's a change to the shared web assets, not the Android wrapper.

## Design choices

- **minSdk 26** (Android 8.0+) specifically so the launcher icon could be a
  pure vector adaptive icon (`res/drawable/ic_launcher_foreground.xml` +
  a solid background color) — no raster PNG generation step needed.
- **Zero library dependencies** — `MainActivity` only touches
  `android.app.Activity`/`android.webkit.*` framework classes, so the build
  doesn't need AndroidX, Capacitor, or any other wrapper toolkit.
- **`INTERNET` permission included** so Google Fonts / the Twemoji CDN can
  still enhance the experience when the device is online — `app.js`
  already degrades gracefully offline (try/catch + native-glyph fallback),
  so this is a nice-to-have, not a requirement.
