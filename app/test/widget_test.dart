// Basic widget tests for Aegis Link app

import 'package:flutter_test/flutter_test.dart';

import 'package:app/main.dart';

void main() {
  testWidgets('Permission screen renders correctly',
      (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const AegisLinkApp());

    // Verify that permission screen is displayed
    expect(find.text('Aegis Link Setup'), findsOneWidget);
    expect(find.text('Protect Your Device'), findsOneWidget);
    expect(find.text('Accessibility Service'), findsOneWidget);
    expect(find.text('Display Over Other Apps'), findsOneWidget);
  });
}
