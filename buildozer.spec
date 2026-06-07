[app]
title        = Blood Cell Counter
package.name = bloodcellcounter
package.domain = com.bloodchecker

source.dir  = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,html,css,js
source.include_patterns = bloodchecker_app/**

version = 1.1.0
requirements = python3,kivy,flask,jinja2,werkzeug,click,itsdangerous,markupsafe,reportlab,pyjnius

# Orientation
orientation = portrait
fullscreen  = 0

android.api          = 33
android.minapi       = 21
android.ndk          = 25b
android.sdk          = 33
android.arch         = arm64-v8a

# Permissions
android.permissions  = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Icons / presplash (optional — replace with your own)
# icon.filename       = %(source.dir)s/icon.png
# presplash.filename  = %(source.dir)s/presplash.png

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
