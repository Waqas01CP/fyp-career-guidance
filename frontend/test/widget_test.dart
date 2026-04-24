import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fyp_career_guidance/main.dart';

void main() {
  testWidgets('App smoke test — launches without crash', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: FypApp()));
    // AppRouter shows a loading spinner while resolving route
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
