import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
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
      _navigate('/onboarding');
      return;
    }
    await ref.read(profileProvider.notifier).loadProfile(token);
    final profile = ref.read(profileProvider);
    if (profile.error == 'session_expired') {
      ref.read(authProvider.notifier).handleUnauthorized();
      _navigate('/onboarding');
      return;
    }
    if (profile.error != null) {
      // Network or server error — safe fallback to onboarding
      _navigate('/onboarding');
      return;
    }
    _navigate(_routeForStage(profile.onboardingStage));
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

  void _navigate(String route) {
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, route);
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
