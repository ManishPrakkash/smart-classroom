# Smart Classroom Mobile App - Deployment Guide

## 📱 Mobile App Successfully Created!

Your React web app has been converted to native Android and iOS applications using Capacitor.

## Project Structure

```
frontend/
├── android/              # Native Android project
├── ios/                  # Native iOS project (requires macOS to build)
├── dist/                 # Web build output
├── src/                  # React source code
├── capacitor.config.ts   # Capacitor configuration
└── package.json          # Dependencies and build scripts
```

## ⚙️ Configuration

### Update API Base URL

Before building for production, update the Raspberry Pi IP address:

**File: [src/config.js](file:///w:/VSCODE/Hardware-Project/frontend/src/config.js)**

```javascript
if (isNative()) {
  return 'http://192.168.1.100:5000';  // ⚠️ CHANGE THIS to your Pi's IP
}
```

**How to find your Raspberry Pi's IP:**
```bash
# On Raspberry Pi
hostname -I
# Or
ip addr show
```

## 📦 Building the App

### Android Build

#### Requirements
- **Android Studio** installed
- **Java Development Kit (JDK)** 11 or later
- Android SDK (installed with Android Studio)

#### Steps

1. **Open Android Studio**
   ```bash
   npm run android:build
   ```
   This will:
   - Build the React app
   - Sync assets to Android
   - Open Android Studio

2. **In Android Studio**
   - Wait for Gradle sync to complete
   - Click "Run" or press `Shift+F10`
   - Select a connected device or emulator
   - App will install and launch!

3. **Build APK for Distribution**
   - **Menu**: Build → Build Bundle(s) / APK(s) → Build APK(s)
   - APK location: `android/app/build/outputs/apk/debug/app-debug.apk`
   - Transfer to Android device and install

#### Release Build (Signed APK)

1. **Generate Signing Key**
   ```bash
   cd android
   keytool -genkey -v -keystore smartclassroom.keystore -alias smartclassroom -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Configure in Android Studio**
   - File → Project Structure → Modules → Signing Configs
   - Add release config with keystore details

3. **Build Signed APK**
   - Build → Generate Signed Bundle / APK
   - Select APK → Next
   - Choose keystore → Build

### iOS Build (macOS Only)

#### Requirements
- **macOS** computer
- **Xcode** 14+ installed
- **Apple Developer Account** ($99/year for device testing & App Store)

#### Steps

1. **Open Xcode**
   ```bash
   npm run ios:build
   ```

2. **Configure Signing**
   - Select project in navigator
   - Select "App" target
   - Signing & Capabilities tab
   - Select your Team (Developer account)

3. **Run on Simulator**
   - Select iPhone simulator from device menu
   - Click Run (▶️) or press `Cmd+R`

4. **Run on Physical Device**
   - Connect iPhone via USB
   - Trust computer on device
   - Select device from menu
   - Click Run

5. **Build for App Store**
   - Product → Archive
   - Distribute App → App Store Connect
   - Follow upload wizard

## 🌐 Network Configuration

### Local Network Access

**Requirements:**
- Mobile device and Raspberry Pi on **same WiFi network**
- Flask backend running on Pi

**Backend Configuration:**

```python
# backend/app.py
# Already configured - Flask binds to 0.0.0.0
app.run(host="0.0.0.0", port=5000)
```

### Android Network Permissions

Already configured in `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### Testing Network Connection

1. Start Flask backend on Raspberry Pi
2. Find Pi's IP (e.g., `192.168.1.100`)
3. Update `src/config.js` with correct IP
4. Rebuild app: `npm run build && npx cap sync`
5. Run app on mobile device
6. App should connect and show devices!

## 🔧 Development Commands

```bash
# Build web app
npm run build

# Sync web assets to native projects
npx cap sync

# Open Android Studio
npx cap open android

# Open Xcode (macOS)
npx cap open ios

# Build and open (Android)
npm run android:build

# Build and open (iOS)
npm run ios:build

# Update Capacitor plugins
npx cap update

# Check Capacitor status
npx cap doctor
```

## 🐛 Troubleshooting

### "Cannot connect to server"

1. ✅ Raspberry Pi and mobile on same WiFi?
2. ✅ Backend running on Pi? (`python app.py`)
3. ✅ Correct IP in `src/config.js`?
4. ✅ Firewall blocking port 5000?
5. ✅ Rebuilt app after changing config? (`npm run build && npx cap sync`)

### Android Studio Issues

**Gradle sync fails:**
```bash
cd android
./gradlew clean
./gradlew build
```

**Build errors:**
- Check JDK version (needs 11+)
- Update Android SDK in SDK Manager
- Invalidate Caches: File → Invalidate Caches / Restart

### iOS Build Issues

**Code signing error:**
- Add Apple ID in Xcode preferences
- Select correct Team in signing settings
- Ensure device is registered in developer portal

**"Untrusted Developer" on device:**
- Settings → General → VPN & Device Management
- Trust the developer profile

## 📱 Testing on Physical Device

### Android (Easiest)

1. **Enable Developer Options**
   - Settings → About Phone
   - Tap "Build Number" 7 times

2. **Enable USB Debugging**
   - Settings → Developer Options → USB Debugging

3. **Connect via USB**
   - Connect phone to computer
   - Allow USB debugging prompt
   - Run from Android Studio

### iOS (Requires Apple Developer)

1. **Register Device**
   - Connect iPhone
   - Xcode → Window → Devices and Simulators
   - Add device to portal

2. **Run on Device**
   - Select device in Xcode
   - Click Run

## 🚀 Distribution

### Android - Google Play Store

1. Create Google Play Console account ($25 one-time fee)
2. Build signed release AAB (Android App Bundle)
3. Upload to Play Console
4. Complete store listing
5. Submit for review

### Android - Direct APK Distribution

1. Build release APK
2. Transfer to device (email, USB, cloud)
3. Install APK
4. Allow "Install from Unknown Sources" if needed

### iOS - Apple App Store

1. Apple Developer account ($99/year)
2. Create App ID and provisioning profile
3. Archive in Xcode
4. Upload to App Store Connect
5. Complete app information
6. Submit for review

### iOS - TestFlight (Beta Testing)

1. Upload build to App Store Connect
2. Enable TestFlight testing
3. Add internal/external testers
4. Share invite link

## 🎯 Next Steps

1. **Update Raspberry Pi IP** in `src/config.js`
2. **Test on emulator/simulator** first
3. **Test on physical device** on same network as Pi
4. **Create app icons** (see App Assets section)
5. **Consider features**:
   - Haptic feedback on toggle
   - Push notifications
   - Background refresh
   - Dark/light theme toggle

## 📐 App Assets (Optional)

### App Icon

Place icon files at:
- **Android**: `android/app/src/main/res/mipmap-*/ic_launcher.png`
- **iOS**: `ios/App/App/Assets.xcassets/AppIcon.appiconset/`

Use online generators like:
- https://icon.kitchen/
- https://www.appicon.co/

### Splash Screen

Configure in `capacitor.config.ts`:

```typescript
plugins: {
  SplashScreen: {
    launchShowDuration: 2000,
    backgroundColor: "#0f172a",
    showSpinner: false
  }
}
```

## 📚 Resources

- **Capacitor Docs**: https://capacitorjs.com/docs
- **Android Studio**: https://developer.android.com/studio
- **Xcode**: https://developer.apple.com/xcode/
- **Ionic Icons**: https://ionic.io/ionicons (for adding icons to app)

## ✅ Summary

Your Smart Classroom app is now:
- ✅ Native Android app
- ✅ Native iOS app
- ✅ Network monitoring enabled
- ✅ Production-ready build
- ✅ Ready for testing and deployment

**Current Status**: Ready to test on Android/iOS devices!
