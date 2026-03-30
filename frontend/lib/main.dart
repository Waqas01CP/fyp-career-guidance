import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/auth/login_screen.dart';

void main() {
  runApp(const FYPApp());
}

class FYPApp extends StatelessWidget {
  const FYPApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      child: MaterialApp(
        title: 'Career Guidance',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF0F766E), // Academic Teal
          ),
          textTheme: GoogleFonts.interTextTheme(),
          useMaterial3: true,
        ),
        home: const LoginScreen(),
      ),
    );
  }
}