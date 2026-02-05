import 'package:flutter/material.dart';
import '../services/native_bridge.dart';

/// Permission setup screen for Aegis Link app.
/// Guides users through enabling accessibility and overlay permissions.
class PermissionScreen extends StatefulWidget {
  const PermissionScreen({super.key});

  @override
  State<PermissionScreen> createState() => _PermissionScreenState();
}

class _PermissionScreenState extends State<PermissionScreen>
    with WidgetsBindingObserver {
  bool _accessibilityEnabled = false;
  bool _overlayEnabled = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _checkPermissions();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _checkPermissions();
    }
  }

  Future<void> _checkPermissions() async {
    setState(() => _isLoading = true);

    final accessibilityEnabled =
        await NativeBridge.instance.isAccessibilityEnabled();
    final overlayEnabled =
        await NativeBridge.instance.isOverlayPermissionGranted();

    setState(() {
      _accessibilityEnabled = accessibilityEnabled;
      _overlayEnabled = overlayEnabled;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E21),
      appBar: AppBar(
        title: const Text('Aegis Link Setup'),
        backgroundColor: const Color(0xFF1D1E33),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  const Icon(
                    Icons.shield,
                    size: 80,
                    color: Color(0xFF4CAF50),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Protect Your Device',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Enable the required permissions to activate smishing protection.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 40),

                  // Accessibility Permission Card
                  _PermissionCard(
                    icon: Icons.accessibility_new,
                    title: 'Accessibility Service',
                    description:
                        'Required to detect suspicious URLs in messages and browsers.',
                    isEnabled: _accessibilityEnabled,
                    onTap: () =>
                        NativeBridge.instance.openAccessibilitySettings(),
                  ),
                  const SizedBox(height: 16),

                  // Overlay Permission Card
                  _PermissionCard(
                    icon: Icons.layers,
                    title: 'Display Over Other Apps',
                    description:
                        'Required to show warning overlay when suspicious URL is detected.',
                    isEnabled: _overlayEnabled,
                    onTap: () =>
                        NativeBridge.instance.requestOverlayPermission(),
                  ),
                  const SizedBox(height: 32),

                  // Status
                  if (_accessibilityEnabled && _overlayEnabled) ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF4CAF50).withAlpha(30),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF4CAF50)),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle, color: Color(0xFF4CAF50)),
                          SizedBox(width: 8),
                          Text(
                            'Protection Active',
                            style: TextStyle(
                              color: Color(0xFF4CAF50),
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.orange.withAlpha(30),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.orange),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.warning, color: Colors.orange),
                          SizedBox(width: 8),
                          Text(
                            'Setup Incomplete',
                            style: TextStyle(
                              color: Colors.orange,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}

class _PermissionCard extends StatelessWidget {
  const _PermissionCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.isEnabled,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String description;
  final bool isEnabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1D1E33),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isEnabled ? const Color(0xFF4CAF50) : Colors.white24,
          width: isEnabled ? 2 : 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isEnabled ? null : onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isEnabled
                        ? const Color(0xFF4CAF50).withAlpha(30)
                        : Colors.white.withAlpha(10),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    icon,
                    color: isEnabled ? const Color(0xFF4CAF50) : Colors.white70,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(
                          color: Colors.white60,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  isEnabled ? Icons.check_circle : Icons.arrow_forward_ios,
                  color: isEnabled ? const Color(0xFF4CAF50) : Colors.white54,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
