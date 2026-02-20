[app]
title = Pro Downloader
package.name = prodownloader
package.domain = org.zahirov
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
source.exclude_exts = spec,bak
source.exclude_dirs = venv,bin,downloads,temp_preview,__pycache__,.buildozer,.git,.venv
source.exclude_patterns = *.pyc,*.pyo,*.bak,main.py.bak,requirements.txt,download_history.json
version = 1.0.3

# Minimal dependencies — no plyer, no tiktok-downloader
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,yt-dlp,certifi,urllib3,charset-normalizer,idna

icon.filename = %(source.dir)s/icon.png

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.manifest.intent_filters = intent_filters.xml
android.api = 33
android.minapi = 24
# Single arch — most modern phones are arm64; saves ~25 MB
android.archs = arm64-v8a
android.accept_sdk_license = True

# Strip debug symbols from native libraries
android.strip = True

[buildozer]
log_level = 2
warn_on_root = 1
