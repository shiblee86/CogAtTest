plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.cogatacademy.detective"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.cogatacademy.detective"
        // WebView on API 26+ is Chromium-based and lets the launcher icon be a
        // pure vector adaptive icon (no raster mipmaps to generate offline).
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

// Intentionally zero library dependencies: MainActivity only touches
// android.app.Activity / android.webkit.* framework classes, and the actual
// app is the bundled web asset bundle (see src/main/assets/), not native code.
