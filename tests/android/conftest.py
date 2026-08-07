"""Fixtures for the Android-wrapper test suite.

These tests need a JDK + Android SDK on the machine running pytest -- unlike
the browser-driven web-app suite, there's no way to vendor that toolchain in.
Mirrors the graceful-skip pattern the top-level conftest.py already uses for
a missing Chrome binary: if the toolchain isn't found, these tests report as
*skipped*, not failed, so `pytest` (no filter) still passes cleanly on a
machine that never installed the Android SDK.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANDROID_DIR = REPO_ROOT / "android"


def _find_java_home():
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]
    # Extra candidate location used to provision *this* sandbox -- harmless
    # to check on any machine, since it's just one more place to look.
    for candidate in sorted(Path.home().glob("android-build-tools/jdk-*"), reverse=True):
        if (candidate / "bin" / "java").exists():
            return str(candidate)
    java = shutil.which("java")
    if java:
        return str(Path(java).resolve().parent.parent)
    return None


def _find_android_sdk():
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var):
            return os.environ[var]
    local_props = ANDROID_DIR / "local.properties"
    if local_props.exists():
        for line in local_props.read_text().splitlines():
            if line.startswith("sdk.dir="):
                return line.split("=", 1)[1].strip()
    default = Path.home() / "Android" / "Sdk"
    if default.exists():
        return str(default)
    return None


@pytest.fixture(scope="session")
def android_env():
    java_home = _find_java_home()
    sdk_home = _find_android_sdk()
    if not java_home or not sdk_home:
        pytest.skip(
            "Android SDK/JDK not found -- set JAVA_HOME and ANDROID_HOME "
            "(or android/local.properties) to run the android test suite"
        )
    env = dict(os.environ)
    env["JAVA_HOME"] = java_home
    env["ANDROID_HOME"] = sdk_home
    env["ANDROID_SDK_ROOT"] = sdk_home
    env["PATH"] = f"{java_home}/bin:{env.get('PATH', '')}"

    local_props = ANDROID_DIR / "local.properties"
    if not local_props.exists():
        local_props.write_text(f"sdk.dir={sdk_home}\n")

    return env


@pytest.fixture(scope="session")
def gradlew(android_env):
    path = ANDROID_DIR / "gradlew"
    if not path.exists():
        pytest.skip("android/gradlew not found")
    return str(path)


@pytest.fixture(scope="session")
def debug_apk(android_env, gradlew):
    """Builds (or reuses, via Gradle's own up-to-date checks) the debug APK
    once per test session and returns its path. A real `./gradlew
    assembleDebug` run, same as a developer or CI would do -- not a mock.
    """
    result = subprocess.run(
        [gradlew, "assembleDebug", "--console=plain"],
        cwd=str(ANDROID_DIR),
        env=android_env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if result.returncode != 0:
        pytest.fail(
            "./gradlew assembleDebug failed:\n"
            f"{result.stdout[-4000:]}\n{result.stderr[-4000:]}"
        )
    apk = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    assert apk.exists(), "assembleDebug reported success but the APK is missing"
    return apk


@pytest.fixture(scope="session")
def aapt_binary(android_env):
    build_tools_dir = Path(android_env["ANDROID_HOME"]) / "build-tools"
    if not build_tools_dir.exists():
        pytest.skip("no build-tools installed under the Android SDK")
    for version_dir in sorted(build_tools_dir.iterdir(), reverse=True):
        candidate = version_dir / "aapt"
        if candidate.exists():
            return str(candidate)
    pytest.skip("no aapt binary found in any installed build-tools version")


@pytest.fixture(scope="session")
def badging(aapt_binary, debug_apk):
    result = subprocess.run(
        [aapt_binary, "dump", "badging", str(debug_apk)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout
