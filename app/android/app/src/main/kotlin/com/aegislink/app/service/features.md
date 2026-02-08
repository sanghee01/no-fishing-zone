# AegisLink AccessibilityService Features

## 개요

Android AccessibilityService를 활용하여 화면에 표시되는 URL을 실시간으로 감지하고, 검증 서버를 통해 스미싱을 방지하는 기능.

## 동작 모드

### 1. Universal Intercept Mode (기본값: ON)
- **모든 링크 클릭**을 검증 URL로 리디렉션
- 사전 차단 방식 - 사용자가 안전한 URL만 접근하도록 보장
- `universalInterceptMode = true`

### 2. Suspicious-Only Mode (레거시)
- 의심스러운 URL 패턴에 일치하는 링크만 오버레이 차단
- 사후 경고 방식 - 위험한 패턴 감지 시에만 차단
- `universalInterceptMode = false`

## 모듈 구조

```
service/
├── AegisLinkAccessibilityService.kt  # 메인 서비스 (이벤트 처리, 모드 분기)
├── UniversalLinkInterceptor.kt       # [NEW] 모든 링크 리디렉션 (Universal Mode)
├── UrlScanner.kt                      # 의심 URL 판별 (Suspicious-Only Mode)
├── BrowserUrlExtractor.kt            # 브라우저 주소창 URL 추출
├── TextUrlExtractor.kt               # 화면 텍스트 URL 추출 (현재 비활성)
└── features.md                       # 기능 문서
```

### 모듈별 역할

| 모듈 | 역할 |
|------|------|
| `AegisLinkAccessibilityService` | 이벤트 수신, 모드 분기, 오버레이 표시 |
| `UniversalLinkInterceptor` | **모든** URL을 검증 서버로 리디렉션 |
| `UrlScanner` | **의심 URL만** 판별 + 차단 상태 관리 |
| `BrowserUrlExtractor` | Chrome/Samsung/Firefox 주소창에서 URL 추출 |

## 핵심 기능

### 1. 실시간 URL 모니터링

- **이벤트 타입**:
  - `TYPE_WINDOW_CONTENT_CHANGED`: 화면 콘텐츠 변경 시
  - `TYPE_WINDOW_STATE_CHANGED`: 앱 전환 시 (외부 앱에서 링크 열기)
- **감지 방식**:
  1. 브라우저 주소창 직접 탐색 (`viewIdResourceName`)
  2. 화면 전체 텍스트 URL 패턴 매칭

### 2. 브라우저 주소창 감지 (BrowserUrlExtractor)

| 브라우저 | viewIdResourceName |
|----------|-------------------|
| Chrome | `com.android.chrome:id/url_bar` |
| Samsung Internet | `com.sec.android.app.sbrowser:id/url_bar` |
| Firefox | `org.mozilla.firefox:id/url_bar` |
| Naver Whale | `com.naver.whale:id/url_bar` |

### 3. 감시 대상 앱 (MONITORED_PACKAGES)

| 앱 | 패키지명 |
|---|---|
| 삼성 메시지 | `com.samsung.android.messaging` |
| 구글 메시지 | `com.google.android.apps.messaging` |
| 카카오톡 | `com.kakao.talk` |
| Chrome | `com.android.chrome` |
| Firefox | `org.mozilla.firefox` |
| 삼성 인터넷 | `com.sec.android.app.sbrowser` |
| 네이버 웨일 | `com.naver.whale` |

### 4. Universal Intercept 로직 (NEW)

**동작 원리**:
1. 브라우저 주소창 변경 감지
2. 안전한 URL (`about:`, `chrome://`, `localhost` 등) 필터링
3. **Grace Period 체크**: 검증 페이지 방문 직후인지 확인 (제거됨 - 즉시 차단)
4. **리디렉션**: `{NO_FISHING_ZONE_URL}?url={사용자가 이동하려던 URL}`로 이동
5. **검증 페이지 도달 시**: 쿨다운(3초) 및 처리된 URL 기록 초기화 -> 뒤로가기 시 즉시 재차단 가능

<!-- **주요 파라미터**:
- `PROCESSED_URL_TTL_MS`: 2000ms (2초) - 차단 후 2초 지나면 다시 차단 시도
- `INTERCEPT_COOLDOWN_MS`: 3000ms (3초) - 동일 URL 연속 감지 시 쿨다운 (검증 페이지 도달 시 초기화) -->

### 5. 의심 URL 패턴 (SUSPICIOUS_PATTERNS) - Legacy Mode

현재 테스트용 패턴 목록:
- `forms.gle/*`
- `qr-codes.io/*`
- `*.myfreesites.net`
- `*.godaddysites.com`
- 기타 피싱 사이트 패턴

<!-- ### 6. 차단 오버레이 (Legacy Mode Only)

- **트리거**: 신규 의심 URL 감지 시 (Suspicious-Only Mode)
- **동작**:
  1. 전체 화면 오버레이 표시
  2. `performGlobalAction(GLOBAL_ACTION_BACK)` 실행
- **버튼**:
  - **Block and Close**: 검증 페이지로 리다이렉트
  - **Proceed Anyway**: 오버레이만 닫기 -->

## Flutter 연동

- **MethodChannel**: `com.aegislink.app/blocker`
- **제공 메서드**:
  - `isAccessibilityEnabled`: 접근성 서비스 활성화 여부
  - `openAccessibilitySettings`: 접근성 설정 화면 열기
  - `isOverlayPermissionGranted`: 오버레이 권한 여부
  - `requestOverlayPermission`: 오버레이 권한 요청
  - `getBlockedUrls`: 차단된 URL 목록 조회
- **콜백 이벤트**:
  - `onUrlBlocked`: 의심 URL 차단 시 (Legacy Mode)
  - `onUrlIntercepted`: URL 리디렉션 시 (Universal Mode)

## 모드 전환

```kotlin
// Universal Mode (모든 링크 리디렉션) - 기본값
AegisLinkAccessibilityService.universalInterceptMode = true

// Legacy Mode (의심 URL만 차단)
AegisLinkAccessibilityService.universalInterceptMode = false
```

## 필요 권한

- `BIND_ACCESSIBILITY_SERVICE`
- `SYSTEM_ALERT_WINDOW` (오버레이 표시 - Legacy Mode)
