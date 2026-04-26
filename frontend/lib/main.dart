import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:google_fonts/google_fonts.dart';
import 'providers/auth_provider.dart';
import 'providers/profile_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding/carousel_screen.dart';
import 'screens/onboarding/riasec_quiz_screen.dart';
import 'screens/onboarding/riasec_complete_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/signup_screen.dart';
import 'screens/onboarding/grades_input_screen.dart';
import 'screens/onboarding/grades_complete_screen.dart';
import 'screens/onboarding/assessment_screen.dart';
import 'screens/onboarding/assessment_complete_screen.dart';
import 'screens/chat/main_chat_screen.dart';
import 'screens/dashboard/recommendation_dashboard.dart';
import 'screens/profile/settings_screen.dart';
import 'screens/error_screen.dart';

void main() {
  runApp(const ProviderScope(child: FypApp()));
}

class FypApp extends StatelessWidget {
  const FypApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(390, 844),
      minTextAdapt: true,
      splitScreenMode: false,
      builder: (context, child) {
        return MaterialApp(
          title: 'AI Career Guidance',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(0xFF006B62),
              brightness: Brightness.light,
            ),
            textTheme: GoogleFonts.interTextTheme(),
            useMaterial3: true,
          ),
          initialRoute: '/',
          onGenerateRoute: (settings) {
            final Map<String, WidgetBuilder> routes = {
              '/': (context) => const SplashScreen(),
              '/onboarding': (context) => const CarouselScreen(),
              '/login': (context) => const LoginScreen(),
              '/signup': (context) => const SignupScreen(),
              '/forgot-password': (context) =>
                  const _PlaceholderScreen('Forgot Password'),
              '/riasec-quiz': (context) => const RiasecQuizScreen(),
              '/riasec-complete': (context) => const RiasecCompleteScreen(),
              '/grades-input': (context) => const GradesInputScreen(),
              '/grades-complete': (context) => const GradesCompleteScreen(),
              '/assessment': (context) => const AssessmentScreen(),
              '/assessment-complete': (context) =>
                  const AssessmentCompleteScreen(),
              '/chat': (context) => const MainChatScreen(),
              '/dashboard': (context) => const RecommendationDashboard(),
              '/profile': (context) =>
                  const _PlaceholderScreen('Student Profile'),
              '/settings': (context) => const SettingsScreen(),
              '/error': (context) {
                final args =
                    settings.arguments as Map<String, dynamic>?;
                final errorType =
                    args?['errorType'] as ErrorType? ?? ErrorType.noNetwork;
                return ErrorScreen(errorType: errorType);
              },
            };

            final builder = routes[settings.name];
            if (builder == null) return null;

            return PageRouteBuilder(
              settings: settings,
              pageBuilder: (context, animation, _) => builder(context),
              transitionsBuilder: (context, animation, _, child) =>
                  FadeTransition(
                opacity: CurvedAnimation(
                  parent: animation,
                  curve: Curves.easeInOut,
                ),
                child: child,
              ),
              transitionDuration: const Duration(milliseconds: 220),
            );
          },
        );
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
      backgroundColor: Color(0xFF006B62),
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
