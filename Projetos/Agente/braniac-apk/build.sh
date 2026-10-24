#!/usr/bin/env bash
# Gera braniac.apk SEM Gradle: aapt2 + javac + d8 + apksigner (SDK em ~/AppData/Local/Android/Sdk, JDK em Program Files).
# Uso: bash braniac-apk/build.sh   -> braniac-apk/dist/BRANIAC.apk
set -e
cd "$(dirname "$0")"
SDK="/c/Users/carlo/AppData/Local/Android/Sdk"; BT="$SDK/build-tools/34.0.0"; JAR="$SDK/platforms/android-34/android.jar"
JDK="/c/Program Files/Java/jdk-26.0.1/bin"
rm -rf build dist && mkdir -p build/res build/gen build/classes dist
"$BT/aapt2.exe" compile --dir res -o build/res.zip
"$BT/aapt2.exe" link -o build/base.apk -I "$JAR" --manifest AndroidManifest.xml -A assets --java build/gen --min-sdk-version 24 --target-sdk-version 34 build/res.zip
"$JDK/javac.exe" --release 11 -cp "$JAR" -d build/classes build/gen/com/braniac/app/R.java src/com/braniac/app/MainActivity.java
(cd build/classes && "$JDK/jar.exe" cf ../app.jar .)
"$BT/d8.bat" --release --lib "$(cygpath -w "$JAR")" --min-api 24 --output build build/app.jar
cp build/base.apk build/unsigned.apk
(cd build && "$JDK/jar.exe" uf unsigned.apk classes.dex)
"$BT/zipalign.exe" -f -p 4 build/unsigned.apk build/aligned.apk
[ -f braniac.keystore ] || "$JDK/keytool.exe" -genkeypair -keystore braniac.keystore -alias braniac -keyalg RSA -keysize 2048 -validity 10000 -storepass braniac -keypass braniac -dname "CN=BRANIAC"
"$BT/apksigner.bat" sign --ks braniac.keystore --ks-pass pass:braniac --key-pass pass:braniac --out dist/BRANIAC.apk build/aligned.apk
ls -la dist
