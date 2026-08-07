"""Regression guard on the built APK's manifest: package identity, the
launcher activity, declared permissions, and min SDK are all things that
should only change deliberately, not as a side effect of an unrelated
Gradle/manifest edit. Verified via `aapt dump badging` against the real
built APK, not by parsing the source AndroidManifest.xml -- this catches
merger/build-time mistakes too, not just source typos.
"""
import re

import pytest

pytestmark = pytest.mark.android


def test_package_name_is_stable(badging):
    assert "package: name='com.cogatacademy.detective'" in badging


def test_launcher_activity_is_main_activity(badging):
    assert "launchable-activity: name='com.cogatacademy.detective.MainActivity'" in badging


def test_internet_permission_is_declared(badging):
    # Lets Google Fonts / the Twemoji CDN enhance the experience when
    # online; app.js already degrades gracefully offline (see DESIGN.md).
    assert "uses-permission: name='android.permission.INTERNET'" in badging


def test_min_sdk_is_26_or_higher(badging):
    # minSdk 26 was chosen specifically so the launcher icon could stay a
    # pure vector adaptive icon (see android/README.md) -- a regression
    # below 26 would silently break that assumption.
    match = re.search(r"sdkVersion:'(\d+)'", badging)
    assert match, badging
    assert int(match.group(1)) >= 26


def test_app_label_matches_branding(badging):
    assert "application-label:'CogAT Detective Academy'" in badging
