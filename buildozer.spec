[app]

package.name = livebooster
package.domain = com.livebooster.app
title = LIVE BOOSTER

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,mp3,wav
main.py = main.py

version = 1.0
orientation = all

android.permissions = INTERNET, ACCESS_NETWORK_STATE, FOREGROUND_SERVICE, POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED, WAKE_LOCK, QUERY_ALL_PACKAGES, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, REQUEST_INSTALL_PACKAGES, PACKAGE_USAGE_STATS

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

requirements = python3, kivy==2.3.0, kivymd==1.1.1, plyer, pyjnius, pillow, requests, schedule, android
android.hostpython3 = /usr/bin/python3.10
p4a.branch = develop

icon.filename = assets/icon.png
intent.filters = livebooster://

fullscreen = 0
presplash.color = #FF0000
