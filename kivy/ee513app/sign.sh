jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/keystores/ie-dcu-ee513-axlapp.keystore bin/axlapp-0.1-armeabi-v7a-release-unsigned.apk ee513
zipalign -v 4 bin/axlapp-0.1-armeabi-v7a-release-unsigned.apk bin/axlapp-0.1-armeabi-v7a-release-signed.apk
