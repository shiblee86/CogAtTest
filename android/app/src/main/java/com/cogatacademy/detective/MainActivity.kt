package com.cogatacademy.detective

import android.app.Activity
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient

/**
 * The entire app is the existing static web app (index.html/app.js/styles.css
 * + assets/), bundled unmodified under src/main/assets/ and loaded from
 * file:///android_asset/. This Activity is just a WebView host: all state,
 * question generation, and rendering logic still lives in app.js.
 */
class MainActivity : Activity() {

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        webView.settings.apply {
            javaScriptEnabled = true
            // Progress (mastery/stats/mistakes/daily mission) is persisted via
            // localStorage in app.js -- without this it would silently vanish
            // on every app restart.
            domStorageEnabled = true
            allowFileAccess = true
        }
        webView.webViewClient = WebViewClient()
        // WebChromeClient is required for window.speechSynthesis (Sentence
        // Completion's read-aloud) to reach the platform TTS engine.
        webView.webChromeClient = WebChromeClient()

        if (savedInstanceState == null) {
            webView.loadUrl("file:///android_asset/index.html")
        }
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        // The app is a single page with no in-app navigation history (no
        // pushState/routing), so canGoBack() is realistically always false --
        // this just future-proofs against that changing.
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}
