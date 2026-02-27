# Capacitor Android Build Documentation

This document outlines the steps performed to set up Capacitor for the **Smart Classroom** Vite frontend, add the Android platform, configure the Android SDK, and generate a debug APK.

## 1. Capacitor Initialization
```bash
cd w:/VSCODE/smart-classroom/frontend
npx cap init "Smart Classroom" "com.smartclassroom.app" --web-dir=dist
```
- Created `capacitor.config.ts` with `appId: "com.smartclassroom.app"` and `webDir: "dist"`.

## 2. Build the Web App
```bash
npm run build
```
- Produced the production web assets in the `dist/` folder.

## 3. Add Android Platform
```bash
npx cap add android
```
- Generated the Android project under `android/`.

## 4. Android SDK Configuration
- Detected missing SDK path.
- Created `android/local.properties` with:
```
sdk.dir=C:\Users\<YourUser>\AppData\Local\Android\sdk
```
(Adjust the path if your SDK is located elsewhere.)

## 5. Build Debug APK
```bash
cd android
./gradlew assembleDebug
```
- The build succeeded and produced `app-debug.apk` located at:
```
android/app/build/outputs/apk/debug/app-debug.apk
```

## 6. (Optional) Signed Release Build
If you need a production‑ready APK, you can set up a keystore and run:
```bash
./gradlew assembleRelease
```
- Update `android/gradle.properties` with keystore credentials.
- The signed APK will be at `android/app/build/outputs/apk/release/app-release.apk`.

## 7. Verification
- Install the debug APK on an Android device or emulator:
```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
- Launch the app; it should load the Vite web UI correctly.

---
*Generated on 2026‑02‑27.*
