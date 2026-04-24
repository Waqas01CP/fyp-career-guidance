import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'providers/auth_provider.dart';
import 'providers/profile_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding/carousel_screen.dart';
import 'screens/onboarding/riasec_quiz_screen.dart';
import 'screens/onboarding/riasec_complete_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/signup_screen.dart';

void main() {
  runApp(const ProviderScope(child: FypApp()));
}

class FypApp extends StatelessWidget {
  const FypApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Career Guidance',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6616D7),
          brightness: Brightness.light,
        ),
        textTheme: GoogleFonts.interTextTheme(),
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/onboarding': (context) => const CarouselScreen(),
        '/login': (context) => const LoginScreen(),
        '/signup': (context) => const SignupScreen(),
        '/forgot-password': (context) => const _PlaceholderScreen('Forgot Password'),
        '/riasec-quiz': (context) => const RiasecQuizScreen(),
        '/riasec-complete': (context) => const RiasecCompleteScreen(),
        '/grades-input': (context) => const _PlaceholderScreen('Grades Input'),
        '/grades-complete': (context) => const _PlaceholderScreen('Grades Complete'),
        '/assessment': (context) => const _PlaceholderScreen('Assessment'),
        '/assessment-complete': (context) => const _PlaceholderScreen('Assessment Complete'),
        '/chat': (context) => const _PlaceholderScreen('Chat'),
        '/dashboard': (context) => const _PlaceholderScreen('Dashboard'),
        '/profile': (context) => const _PlaceholderScreen('Student Profile'),
        '/settings': (context) => const _PlaceholderScreen('Settings'),
        '/error': (context) => const _PlaceholderScreen('Network Error'),
      },
    );
  }
}

/// AppRouter — reads auth and profile state on launch,
/// routes to the correct first screen.
class AppRouter extends ConsumerStatefulWidget {
  const AppRouter({super.key});

  @override
  ConsumerState<AppRouter> createState() => _AppRouterState();
}

class _AppRouterState extends ConsumerState<AppRouter> {
  @override
  void initState() {
    super.initState();
    _resolveRoute();
  }

  Future<void> _resolveRoute() async {
    final auth = ref.read(authProvider);
    if (!auth.isAuthenticated) {
      // No token — show onboarding carousel (first install or post-logout)
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.pushReplacementNamed(context, '/onboarding');
      });
      return;
    }

    // Token exists — load profile to get onboarding_stage
    await ref.read(profileProvider.notifier).loadProfile(auth.token!);
    final profile = ref.read(profileProvider);

    if (profile.error == 'session_expired') {
      ref.read(authProvider.notifier).handleUnauthorized();
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.pushReplacementNamed(context, '/login');
      });
      return;
    }

    // Route based on onboarding_stage
    final route = _routeForStage(profile.onboardingStage);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Navigator.pushReplacementNamed(context, route);
    });
  }

  String _routeForStage(String stage) {
    switch (stage) {
      case 'not_started':
        return '/riasec-quiz';
      case 'riasec_complete':
        return '/grades-input';
      case 'grades_complete':
        return '/assessment';
      case 'assessment_complete':
        return '/chat';
      default:
        return '/riasec-quiz';
    }
  }

  @override
  Widget build(BuildContext context) {
    // Show loading spinner while resolving route
    return const Scaffold(
      backgroundColor: Color(0xFF6616D7),
      body: Center(
        child: CircularProgressIndicator(color: Colors.white),
      ),
    );
  }
}

/// Temporary placeholder — replaced as each screen is built.
class _PlaceholderScreen extends StatelessWidget {
  final String name;
  const _PlaceholderScreen(this.name);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(name)),
      body: Center(
        child: Text(
          '$name Screen\n(Coming soon)',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}
