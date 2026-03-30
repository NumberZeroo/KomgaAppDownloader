[app]
title = Komga Downloader
package.name = komgadownloader
package.domain = org.komga

source.dir = .
source.include_exts = py,kv,png,jpg,ttf,json
source.include_patterns = assets/*, ui/*, src/*

version = 1.0.0

requirements = python3, kivy==2.3.1, requests, pillow, cryptography, openssl, filetype, certifi, urllib3, charset-normalizer, idna
orientation = portrait

android.minapi = 21
android.api = 33
android.ndk = 25b

android.permissions = INTERNET

android.enable_androidx = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1