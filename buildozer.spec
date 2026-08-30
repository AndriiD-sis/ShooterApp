[app]
title = Kotleta In The Space
package.domain = ua.mars
package.name = kotletainthespace

source.dir = .
source.include_exts = py,kv,png,jpg,gif,wav,ttf,mp3,json

source.main = main.py

version = 0.14.4

requirements = python3,kivy,kivymd==1.2.0,plyer
android.archs = arm64-v8a

android.permissions = VIBRATE

orientation = landscape
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1