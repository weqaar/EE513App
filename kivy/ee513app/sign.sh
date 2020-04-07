#32bit
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/keystores/ie-dcu-ee513-sxmitter.keystore bin/sxmitter-1.1-armeabi-v7a-release-unsigned.apk ee513
zipalign -v 4 bin/sxmitter-1.1-armeabi-v7a-release-unsigned.apk bin/sxmitter-1.1-armeabi-v7a-release-signed.apk
#64bit
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/keystores/ie-dcu-ee513-sxmitter.keystore bin/sxmitter-1.1-arm64-v8a-release-unsigned.apk ee513
zipalign -v 4 bin/sxmitter-1.1-arm64-v8a-release-unsigned.apk bin/sxmitter-1.1-arm64-v8a-release-signed.apk
