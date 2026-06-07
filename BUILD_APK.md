# Building the APK — Step-by-Step

## What you need on your machine

| Tool | Install |
|------|---------|
| Ubuntu / Debian (or WSL2) | Any recent version |
| Python 3.10+ | `sudo apt install python3 python3-pip` |
| Java 17 | `sudo apt install openjdk-17-jdk` |
| buildozer | `pip install buildozer` |
| Android SDK/NDK | Downloaded automatically by buildozer |

> **Windows users:** use WSL2 (Windows Subsystem for Linux) — buildozer does not run natively on Windows.

---

## 1 — Install dependencies

```bash
sudo apt update && sudo apt install -y \
    git zip unzip python3-pip python3-venv \
    openjdk-17-jdk autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev
pip install buildozer cython
```

## 2 — Build

```bash
cd path/to/android_build      # this folder
buildozer android debug
```

Buildozer will download the Android SDK + NDK (~1 GB) on first run. Grab a coffee — it takes 10–30 min the first time.

The finished APK lands at:
```
android_build/bin/bloodcellcounter-1.1.0-arm64-v8a-debug.apk
```

## 3 — Install on your phone

Enable **Settings → Developer options → USB debugging**, connect via USB, then:

```bash
adb install bin/bloodcellcounter-1.1.0-arm64-v8a-debug.apk
```

Or simply copy the APK to your phone and open it (allow "Install from unknown sources").

---

## How the app works

The APK bundles Python + Flask. On launch it:
1. Starts a local Flask server on `127.0.0.1:5050` in a background thread.
2. Opens an Android WebView pointed at that local server.

The result looks and feels like a native app but runs the exact same web UI.

## PDF export

PDF generation uses **ReportLab** (bundled). Tap **📄 PDF** → **⬇ Download PDF** — the file is saved to your Downloads folder.

## Data storage

`saves.json` is written to the app's home directory on device — data persists between sessions.
