import 'package:flutter/material.dart';
import 'services/native_bridge.dart';
import 'screens/permission_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize native bridge
  await NativeBridge.instance.initialize();

  runApp(const AegisLinkApp());
}

class AegisLinkApp extends StatelessWidget {
  const AegisLinkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aegis Link',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4CAF50),
          brightness: Brightness.dark,
        ),
      ),
      home: const PermissionScreen(),
    );
  }
}
