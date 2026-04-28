import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _surfaceLow = Color(0xFFF7F9FB);

  Widget _buildRetakeCard({
    required String title,
    required String description,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return RetakeCard(
      title: title,
      description: description,
      icon: icon,
      onTap: onTap,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _surfaceLow,
      appBar: AppBar(
        backgroundColor: _surfaceLow,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: _secondary, size: 24.r),
          onPressed: () => Navigator.maybePop(context),
        ),
        title: Text(
          'Student Profile',
          style: TextStyle(
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
            color: _onSurface,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Profile Header
            Center(
              child: Container(
                width: 80.r,
                height: 80.r,
                decoration: const BoxDecoration(
                  color: Color(0xFFEADDFF),
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: Icon(Icons.person, size: 40.r, color: Color(0xFF6616D7)),
              ),
            ),
            SizedBox(height: 16.h),
            Center(
              child: Text(
                'My Assessments',
                style: TextStyle(
                  fontSize: 22.sp,
                  fontWeight: FontWeight.w700,
                  color: _onSurface,
                ),
              ),
            ),
            SizedBox(height: 8.h),
            Center(
              child: Text(
                'Update your profile to get the most accurate recommendations.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: _secondary,
                  height: 1.5,
                ),
              ),
            ),
            SizedBox(height: 32.h),

            // Retake Actions
            Text(
              'RETAKE ASSESSMENTS',
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
                color: _secondary,
                letterSpacing: 1.0,
              ),
            ),
            SizedBox(height: 16.h),
            _buildRetakeCard(
              title: 'Personality & Interests',
              description: 'Update your RIASEC personality profile',
              icon: Icons.psychology,
              onTap: () => Navigator.pushNamed(context, '/riasec-quiz', arguments: {'isRetake': true}),
            ),
            SizedBox(height: 12.h),
            _buildRetakeCard(
              title: 'Academic Grades',
              description: 'Update your examination marks',
              icon: Icons.school,
              onTap: () => Navigator.pushNamed(context, '/grades-input', arguments: {'isRetake': true}),
            ),
            SizedBox(height: 12.h),
            _buildRetakeCard(
              title: 'Capabilities Assessment',
              description: 'Update your subject capabilities',
              icon: Icons.auto_awesome,
              onTap: () => Navigator.pushNamed(context, '/assessment', arguments: {'isRetake': true}),
            ),
            SizedBox(height: 48.h),

            // Settings link
            Center(
              child: TextButton.icon(
                onPressed: () => Navigator.pushNamed(context, '/settings'),
                icon: Icon(Icons.settings, size: 18.r, color: _secondary),
                label: Text(
                  'App Settings',
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w600,
                    color: _secondary,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class RetakeCard extends StatefulWidget {
  final String title;
  final String description;
  final IconData icon;
  final VoidCallback onTap;

  const RetakeCard({
    super.key,
    required this.title,
    required this.description,
    required this.icon,
    required this.onTap,
  });

  @override
  State<RetakeCard> createState() => _RetakeCardState();
}

class _RetakeCardState extends State<RetakeCard> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.97 : 1.0,
        duration: const Duration(milliseconds: 150),
        child: Container(
          padding: EdgeInsets.all(20.r),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16.r),
            boxShadow: const [
              BoxShadow(
                color: Color(0x0A334155),
                blurRadius: 10,
                offset: Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 48.r,
                height: 48.r,
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F4F6),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                alignment: Alignment.center,
                child: Icon(widget.icon, color: const Color(0xFF006B62), size: 24.r),
              ),
              SizedBox(width: 16.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.title,
                      style: TextStyle(
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFF191C1E),
                      ),
                    ),
                    SizedBox(height: 4.h),
                    Text(
                      widget.description,
                      style: TextStyle(
                        fontSize: 13.sp,
                        color: const Color(0xFF515F74),
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: const Color(0xFFBDC9C6), size: 24.r),
            ],
          ),
        ),
      ),
    );
  }
}
