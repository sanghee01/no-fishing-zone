# AegisLink: 스미싱 방지 기술 소개

## 1. 개요: 스마트폰의 "보안관" (AccessibilityService)

AegisLink는 Android 운영체제가 제공하는 **AccessibilityService (접근성 서비스)**를 활용하여 동작합니다.
이 서비스는 본래 시각 장애인을 위해 화면의 내용을 읽어주는 기능을 수행하지만, 보안 앱에서는 화면에 표시되는 **위험한 정보를 실시간으로 감지하는 "눈"** 역할을 합니다.

- **역할**: 사용자가 보고 있는 브라우저 주소창의 URL을 실시간으로 읽어들임
- **권한**: 사용자가 설정에서 직접 권한을 허용해야만 동작

## 2. 감지 및 리디렉션 메커니즘 (어떤 Android API가 작동하나요?)

AegisLink가 사용자의 브라우저 이동을 가로채고 **안전한 검증 페이지로 강제 이동(리디렉션)**시키는 기술적 과정입니다.

### [단계 1] 주소창 읽기: `AccessibilityNodeInfo`
사용자가 브라우저를 켤 때마다 안드로이드는 `AccessibilityEvent`를 발생시킵니다.
AegisLink는 이 이벤트를 잡아서 **`AccessibilityNodeInfo` API**를 사용해 브라우저 주소창의 텍스트(URL)를 가져옵니다.

- **사용 API**: `findAccessibilityNodeInfosByViewId(...)`
- **동작**: 현재 활성화된 브라우저 앱(Chrome 등)의 주소창 ID를 찾아 그 안의 텍스트를 추출합니다.

### [단계 2] 리디렉션 명령: `Intent (ACTION_VIEW)`
위험하다고 판단되거나 검사가 필요한 URL이라면, AegisLink는 안드로이드 시스템에 **"이 주소로 당장 이동해!"**라는 명령을 내립니다. 이것이 **Intent**입니다.

- **사용 API**: `startActivity(Intent(ACTION_VIEW, Uri.parse(검증URL)))`
- **동작**: 
  1. 원래 사용자가 가려던 URL: `http://malicious.com`
  2. AegisLink가 만든 검증 URL: `{NO_FISHING_ZONE_URL}?url=http://malicious.com`
  3. 안드로이드 OS는 `Intent` 명령을 받아 브라우저에게 **검증 URL을 열도록 강제**합니다.
  
결과적으로 사용자는 원래 사이트 대신 AegisLink의 안전한 검증 페이지를 보게 됩니다.

## 3. Flutter와 Android의 협업 구조

이 앱은 **Flutter(Screen)**와 **Android Native(Module)**가 협력하여 동작합니다.

| 영역 | 기술(Language) | 역할 | 기능 |
|:---:|:---:|:---:|:---|
| **Android Native** | Kotlin / Java | **Module** | - 접근성 서비스 구동<br>- **주소창 URL 감지 및 리디렉션 수행** |
| **Flutter** | Dart | **Screen** | - 설정 화면 제공 |
