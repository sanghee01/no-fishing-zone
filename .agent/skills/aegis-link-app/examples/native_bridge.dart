import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Android Native(Kotlin)와 통신하는 브릿지 클래스.
/// 싱글톤 패턴으로 앱 전체에서 하나의 인스턴스만 사용합니다.
class NativeBridge {
  NativeBridge._();
  static final NativeBridge instance = NativeBridge._();

  static const String _channelName = 'com.aegislink.app/blocker';
  final MethodChannel _channel = const MethodChannel(_channelName);

  /// 차단된 URL 이벤트 스트림 컨트롤러
  final StreamController<BlockedUrlEvent> _blockedUrlController =
      StreamController<BlockedUrlEvent>.broadcast();

  /// 차단된 URL 이벤트를 구독할 수 있는 스트림
  Stream<BlockedUrlEvent> get onUrlBlocked => _blockedUrlController.stream;

  /// 브릿지 초기화. 앱 시작 시 한 번 호출합니다.
  Future<void> initialize() async {
    _channel.setMethodCallHandler(_handleMethodCall);
    debugPrint('[NativeBridge] Initialized');
  }

  /// Native에서 호출하는 메서드 핸들러
  Future<dynamic> _handleMethodCall(MethodCall call) async {
    switch (call.method) {
      case 'onUrlBlocked':
        final args = call.arguments as Map<dynamic, dynamic>;
        final event = BlockedUrlEvent(
          url: args['url'] as String,
          appPackage: args['app'] as String,
          timestamp:
              DateTime.fromMillisecondsSinceEpoch(args['timestamp'] as int),
        );
        _blockedUrlController.add(event);
        debugPrint('[NativeBridge] URL blocked: ${event.url}');
        return null;

      default:
        throw PlatformException(
          code: 'UNKNOWN_METHOD',
          message: 'Unknown method: ${call.method}',
        );
    }
  }

  /// 접근성 서비스가 활성화되어 있는지 확인합니다.
  Future<bool> isAccessibilityEnabled() async {
    try {
      final result =
          await _channel.invokeMethod<bool>('isAccessibilityEnabled');
      return result ?? false;
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error checking accessibility: ${e.message}');
      return false;
    }
  }

  /// 접근성 설정 화면을 엽니다.
  Future<void> openAccessibilitySettings() async {
    try {
      await _channel.invokeMethod<void>('openAccessibilitySettings');
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error opening settings: ${e.message}');
    }
  }

  /// 오버레이 권한이 허용되어 있는지 확인합니다.
  Future<bool> isOverlayPermissionGranted() async {
    try {
      final result =
          await _channel.invokeMethod<bool>('isOverlayPermissionGranted');
      return result ?? false;
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error checking overlay: ${e.message}');
      return false;
    }
  }

  /// 오버레이 권한 요청 화면을 엽니다.
  Future<void> requestOverlayPermission() async {
    try {
      await _channel.invokeMethod<void>('requestOverlayPermission');
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error requesting overlay: ${e.message}');
    }
  }

  /// 차단된 URL 목록을 가져옵니다.
  Future<List<String>> getBlockedUrls() async {
    try {
      final result =
          await _channel.invokeMethod<List<dynamic>>('getBlockedUrls');
      return result?.cast<String>() ?? [];
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error getting blocked URLs: ${e.message}');
      return [];
    }
  }

  /// 리소스 해제. 앱 종료 시 호출합니다.
  void dispose() {
    _blockedUrlController.close();
  }
}

/// 차단된 URL 이벤트 데이터 클래스
class BlockedUrlEvent {
  const BlockedUrlEvent({
    required this.url,
    required this.appPackage,
    required this.timestamp,
  });

  final String url;
  final String appPackage;
  final DateTime timestamp;

  @override
  String toString() =>
      'BlockedUrlEvent(url: $url, app: $appPackage, time: $timestamp)';
}

// =============================================================================
// 사용 예시
// =============================================================================
//
// 1. main.dart에서 초기화:
//
//    void main() async {
//      WidgetsFlutterBinding.ensureInitialized();
//      await NativeBridge.instance.initialize();
//      runApp(const MyApp());
//    }
//
// 2. 권한 확인 및 요청:
//
//    final bridge = NativeBridge.instance;
//    
//    if (!await bridge.isAccessibilityEnabled()) {
//      await bridge.openAccessibilitySettings();
//    }
//    
//    if (!await bridge.isOverlayPermissionGranted()) {
//      await bridge.requestOverlayPermission();
//    }
//
// 3. 차단 이벤트 구독:
//
//    NativeBridge.instance.onUrlBlocked.listen((event) {
//      showDialog(
//        context: context,
//        builder: (_) => AlertDialog(
//          title: const Text('⚠️ 스미싱 차단'),
//          content: Text('차단된 URL: ${event.url}\n앱: ${event.appPackage}'),
//        ),
//      );
//    });
//
