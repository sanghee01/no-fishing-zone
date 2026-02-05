import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Bridge class for communication with Android Native (Kotlin).
/// Uses singleton pattern for app-wide access.
class NativeBridge {
  NativeBridge._();
  static final NativeBridge instance = NativeBridge._();

  static const String _channelName = 'com.aegislink.app/blocker';
  final MethodChannel _channel = const MethodChannel(_channelName);

  /// Stream controller for blocked URL events
  final StreamController<BlockedUrlEvent> _blockedUrlController =
      StreamController<BlockedUrlEvent>.broadcast();

  /// Stream to subscribe to blocked URL events
  Stream<BlockedUrlEvent> get onUrlBlocked => _blockedUrlController.stream;

  /// Initialize the bridge. Call once at app startup.
  Future<void> initialize() async {
    _channel.setMethodCallHandler(_handleMethodCall);
    debugPrint('[NativeBridge] Initialized');
  }

  /// Handles method calls from Native side
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

  /// Checks if accessibility service is enabled.
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

  /// Opens accessibility settings page.
  Future<void> openAccessibilitySettings() async {
    try {
      await _channel.invokeMethod<void>('openAccessibilitySettings');
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error opening settings: ${e.message}');
    }
  }

  /// Checks if overlay permission is granted.
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

  /// Opens overlay permission request page.
  Future<void> requestOverlayPermission() async {
    try {
      await _channel.invokeMethod<void>('requestOverlayPermission');
    } on PlatformException catch (e) {
      debugPrint('[NativeBridge] Error requesting overlay: ${e.message}');
    }
  }

  /// Gets list of blocked URLs.
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

  /// Dispose resources. Call when app is closing.
  void dispose() {
    _blockedUrlController.close();
  }
}

/// Blocked URL event data class
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
