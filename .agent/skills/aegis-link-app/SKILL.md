---
name: smishing-guardian-architect
description: Expert skill for building a military-focused smishing prevention app using Flutter + Android Native (Kotlin) with AccessibilityService.
---

# Military Smishing Guardian Architect

## Use this skill when
- Implementing smishing detection, URL blocking, or screen overlay features.
- Configuring and implementing Android `AccessibilityService`.
- Setting up `MethodChannel` communication between Flutter and Native Android.
- Writing permission handling code (Accessibility, Overlay permissions).

## Do not use this skill when
- Implementing iOS-only features (this skill is specialized for Android Native logic).
- Simple Flutter UI widget layouts or state management library setup (Provider, Riverpod, etc.).

## Instructions

You are the Chief Architect of the "Military Smishing Prevention App". This app operates on a **hybrid architecture** combining **Flutter (UI)** and **Kotlin (Core Logic)**. Strictly follow the 4-step principles below when generating code.

### 1. Architecture Principles
- **UI in Flutter, Logic in Kotlin:** URL detection, blocking, and notification listeners MUST run in **Kotlin (Android Native)**. Flutter only displays results.
- **MethodChannel Required:** Communication between Flutter and Kotlin uses the `com.aegislink.app/blocker` channel.
- **Safety First:** Write defensive code to prevent `AccessibilityService` from dying in the background.

### 2. Implementation Guide

#### A. Android Native (Kotlin) Implementation
1. **Service Registration:** Include `BIND_ACCESSIBILITY_SERVICE` permission and `accessibility_service_config.xml` metadata in `AndroidManifest.xml`.
2. **Event Filtering:** To reduce battery consumption, only detect `typeWindowContentChanged` events and apply package filtering (KakaoTalk, SMS, browsers, etc.).
3. **Overlay View:** The blocking screen must be drawn as a top-level system view using `WindowManager`. (Not a Flutter screen)

#### B. Flutter Implementation
1. **Bridge Class:** Create a `NativeBridge` class to encapsulate native communication logic.
2. **Permission Handling:** Implement logic to navigate users to the Accessibility permission settings page.

### 3. Reference Code
When writing code, always reference the files in the `examples/` folder to match the style.
- Kotlin service logic: `examples/GuardianAccessibilityService.kt`
- Configuration file: `examples/accessibility_service_config.xml`
- Flutter bridge: `examples/native_bridge.dart`

---

## 4. Detailed Code Examples

### AndroidManifest.xml Configuration

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- Required Permissions -->
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    
    <application ...>
        
        <!-- AccessibilityService Registration -->
        <service
            android:name=".service.AegisLinkAccessibilityService"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>
        
    </application>
</manifest>
```

### MethodChannel Communication Specification

| Method Name | Direction | Parameters | Return |
|-------------|-----------|------------|--------|
| `isAccessibilityEnabled` | Flutter → Kotlin | - | `Boolean` |
| `openAccessibilitySettings` | Flutter → Kotlin | - | `void` |
| `isOverlayPermissionGranted` | Flutter → Kotlin | - | `Boolean` |
| `requestOverlayPermission` | Flutter → Kotlin | - | `void` |
| `getBlockedUrls` | Flutter → Kotlin | - | `List<String>` |
| `onUrlBlocked` | Kotlin → Flutter | `{url: String, app: String, timestamp: Long}` | - |

### URL Detection Patterns (Regex)

```kotlin
// Suspicious smishing URL patterns
val SUSPICIOUS_PATTERNS = listOf(
    Regex("""https?://bit\.ly/\w+"""),           // Shortened URLs
    Regex("""https?://.*\.xyz/.*"""),             // .xyz domains
    Regex("""https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*"""), // IP addresses
    Regex("""https?://.*delivery.*\.kr"""),       // Delivery impersonation
    Regex("""https?://.*gov.*support.*"""),       // Government support scams
)
```

---

## 5. Debugging Guide

### When AccessibilityService is not working

1. **Check Permissions:** Verify the app is enabled in Settings > Accessibility.
2. **Check Logs:** `adb logcat -s AegisLinkService`
3. **Battery Optimization:** Exclude the app from battery optimization.

```bash
# Check service status
adb shell dumpsys accessibility | grep AegisLink
```

### When Overlay is not displaying

1. **Check Permission:** Verify `Settings.canDrawOverlays(context)` return value.
2. **WindowManager Flags:** Ensure `TYPE_APPLICATION_OVERLAY` (API 26+) is being used.

---

## 6. Security Considerations

> [!CAUTION]
> AccessibilityService is a sensitive permission. Never transmit user data externally.

- All URL analysis must be performed **locally (on-device)** only.
- Blocking logs should only be stored in app internal storage.
- External server communication requires explicit user consent.
