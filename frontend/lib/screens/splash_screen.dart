import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'error_screen.dart';
import '../providers/auth_provider.dart';
import '../providers/profile_provider.dart';
import '../services/auth_service.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _barWidth;

  static const Color _bgColor = Color(0xFF006B62);
  static const Color _barFillColor = Color(0xFF00857A);
  static const Color _taglineColor = Color(0xFFA3FAEF);

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _barWidth = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _controller.forward();
    _resolveRoute();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _resolveRoute() async {
    await Future.delayed(const Duration(milliseconds: 300));
    final token = await AuthService.getToken();
    if (token == null) {
      _navigateSingle('/onboarding');
      return;
    }
    await ref.read(profileProvider.notifier).loadProfile(token);
    final profile = ref.read(profileProvider);
    if (profile.error == 'session_expired') {
      ref.read(authProvider.notifier).handleUnauthorized();
      // Token was revoked — go to login (not carousel) so the user can
      // log back in without losing their onboarding progress context.
      _navigateSingle('/login');
      return;
    }
    if (profile.error != null) {
      // Network or server error while a valid token exists — go to error screen
      // so the user can retry. Do NOT reset to /login (that causes a "false logout").
      _navigateSingle('/error', arguments: {'errorType': ErrorType.serverTimeout});
      return;
    }
    _reconstructStack(profile.onboardingStage);
  }

  /// Rebuilds the full Navigator back-stack for the current onboarding_stage.
  ///
  /// Without this, killing and relaunching the app mid-onboarding gives a
  /// Navigator stack with only the destination screen. Pressing back → black.
  ///
  /// CRITICAL FIX: Each Navigator call is in its own addPostFrameCallback
  /// (via _pushAfterFrame/_pushChain) so each push is processed in a separate
  /// frame. The old approach stacked all pushes in one callback, causing a race
  /// on slower devices — the "black screen on restore" bug.
  void _reconstructStack(String stage) {
    if (!mounted) return;
    switch (stage) {
      case 'not_started':
        // Start of onboarding — quiz is the only screen.
        _pushAfterFrame('/riasec-quiz', replace: true);

      case 'riasec_complete':
        // Back from grades-input → riasec-complete.
        _pushAfterFrame('/riasec-quiz', replace: true, then: [
          '/riasec-complete',
        ]);

      case 'grades_complete':
        // Full back-stack ending at /assessment — student was mid-assessment
        // when they closed the app. grades_complete stage means grades were
        // submitted but assessment was not, so the active screen must be
        // /assessment, not /grades-complete.
        _pushAfterFrame('/riasec-quiz', replace: true, then: [
          '/riasec-complete',
          '/grades-input',
          '/grades-complete',
          '/assessment',
        ]);

      case 'assessment_complete':
      case 'complete':
        // Chat is the terminal authenticated state — clear entire stack.
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          Navigator.pushNamedAndRemoveUntil(
              context, '/chat', (route) => false);
        });

      default:
        // Unknown/future stage — restore to assessment with full back-stack.
        _pushAfterFrame('/riasec-quiz', replace: true, then: [
          '/riasec-complete',
          '/grades-input',
          '/grades-complete',
          '/assessment',
        ]);
    }
  }

  /// Pushes [route] after the current frame, then chains [then] routes each
  /// in their own subsequent frame.
  ///
  /// Using [replace] = true removes the Splash entry (pushReplacementNamed).
  /// Chaining via nested addPostFrameCallback guarantees each Navigator.push
  /// call is processed in a separate frame, preventing the race condition
  /// where back-stack routes are lost when multiple pushes happen in one frame.
  void _pushAfterFrame(
    String route, {
    bool replace = false,
    List<String> then = const [],
  }) {
    if (!mounted) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (replace) {
        Navigator.pushReplacementNamed(context, route);
      } else {
        Navigator.pushNamed(context, route);
      }
      _pushChain(then, 0);
    });
  }

  /// Recursively pushes each route in [routes] starting at [index], one per
  /// frame, ensuring each Navigator push is isolated to its own render cycle.
  void _pushChain(List<String> routes, int index) {
    if (index >= routes.length) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      Navigator.pushNamed(context, routes[index]);
      _pushChain(routes, index + 1);
    });
  }

  /// Used for pre-auth navigation where no back-stack reconstruction is
  /// needed — just replace splash with the target screen.
  void _navigateSingle(String route, {Object? arguments}) {
    if (!mounted) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, route, arguments: arguments);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildLogo(),
                  SizedBox(height: 20.h),
                  Text(
                    'Academic Intelligence',
                    style: TextStyle(
                      fontSize: 22.sp,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      letterSpacing: -0.44,
                    ),
                  ),
                  SizedBox(height: 8.h),
                  Text(
                    'Your Career Companion',
                    style: TextStyle(
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w400,
                      color: _taglineColor,
                      height: 1.6,
                    ),
                  ),
                  SizedBox(height: 48.h),
                  _buildLoadingBar(),
                ],
              ),
            ),
            if (kDebugMode)
              Positioned(
                bottom: 20,
                left: 0,
                right: 0,
                child: Text(
                  'DEBUG BUILD',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 9.sp,
                    fontWeight: FontWeight.w700,
                    color: _taglineColor,
                    letterSpacing: 0.72,
                    height: 1.0,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return SizedBox(
      width: 80.w,
      height: 80.h,
      child: Stack(
        children: [
          Container(
            width: 80.w,
            height: 80.h,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20.r),
            ),
            child: Icon(
              Icons.auto_stories,
              size: 40.r,
              color: Colors.white,
            ),
          ),
          Positioned(
            bottom: 4,
            right: 4,
            child: Icon(
              Icons.auto_awesome,
              size: 16.r,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingBar() {
    return Container(
      width: 120.w,
      height: 3.h,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(2.r),
      ),
      child: AnimatedBuilder(
        animation: _barWidth,
        builder: (context, _) => Align(
          alignment: Alignment.centerLeft,
          child: Container(
            width: _barWidth.value * 120.w,
            height: 3.h,
            decoration: BoxDecoration(
              color: _barFillColor,
              borderRadius: BorderRadius.circular(2.r),
            ),
          ),
        ),
      ),
    );
  }
}
