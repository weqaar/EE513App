[app]
title = ee513app
package.name = axlapp
package.domain = ie.dcu.ee513
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.3
requirements = python3,kivy,plyer,requests,paho-mqtt,pyjnius,jnius
icon.filename = %(source.dir)s/icons/dcu-logo-icon.png
#Android
orientation = portrait
author = Weqaar Janjua
fullscreen = 0
android.permissions = VIBRATE,INTERNET,ACTIVITY_RECOGNITION
android.arch = armeabi-v7a
#IOS
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0
#OSX
osx.python_version = 3
osx.kivy_version = 1.9.1

[buildozer]
log_level = 2
warn_on_root = 1
