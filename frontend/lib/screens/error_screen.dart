import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// Three-state error screen per DESIGN_HANDOFF.
/// Passed [errorType] via route arguments:
///   Navigator.pushNamed(context, '/error', arguments: {'errorType': ErrorType.noNetwork})
enum ErrorType { noNetwork, serverTimeout, sessionExpired }

class ErrorScreen extends StatelessWidget {
  final ErrorType errorType;
  const ErrorScreen({super.key, required this.errorType});

  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _surfaceLow = Color(0xFFF2F4F6);
  static const Color _error = Color(0xFFBA1A1A);

  _ErrorContent _contentFor(ErrorType type) {
    switch (type) {
      case ErrorType.noNetwork:
        return _ErrorContent(
          icon: Icons.signal_wifi_off,
          iconColor: _error,
          title: 'No Connection',
          body:
              'We couldn\'t reach the server. Please check your Wi-Fi or mobile data and try again.',
          primaryLabel: 'Retry',
          secondaryLabel: null,
        );
      case ErrorType.serverTimeout:
        return _ErrorContent(
          icon: Icons.cloud_off,
          iconColor: _error,
          title: 'Server Unavailable',
          body:
              'The AI server is temporarily unavailable. Please wait a moment and try again.',
          primaryLabel: 'Try Again',
          secondaryLabel: 'Go Back',
        );
      case ErrorType.sessionExpired:
        return _ErrorContent(
          icon: Icons.lock_clock,
          iconColor: _primary,
          title: 'Session Expired',
          body:
              'Your session has expired for security reasons. Please sign in again to continue.',
          primaryLabel: 'Sign In',
          secondaryLabel: null,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final content = _contentFor(errorType);

    return Scaffold(
      backgroundColor: _surfaceLow,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 32.w),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icon circle
                Container(
                  width: 88.r,
                  height: 88.r,
                  decoration: BoxDecoration(
                    color: content.iconColor.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    content.icon,
                    size: 40.r,
                    color: content.iconColor,
                  ),
                ),
                SizedBox(height: 28.h),

                // Title
                Text(
                  content.title,
                  style: TextStyle(
                    fontSize: 24.sp,
                    fontWeight: FontWeight.w700,
                    color: _onSurface,
                    letterSpacing: -0.48,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 12.h),

                // Body
                Text(
                  content.body,
                  style: TextStyle(
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w400,
                    color: _secondary,
                    height: 1.65,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 40.h),

                // Primary CTA
                SizedBox(
                  width: double.infinity,
                  height: 56.h,
                  child: ElevatedButton(
                    onPressed: () => _onPrimaryTap(context),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _primary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16.r),
                      ),
                    ),
                    child: Text(
                      content.primaryLabel,
                      style: TextStyle(
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),

                // Secondary CTA
                if (content.secondaryLabel != null) ...[
                  SizedBox(height: 12.h),
                  SizedBox(
                    width: double.infinity,
                    height: 52.h,
                    child: OutlinedButton(
                      onPressed: () => Navigator.maybePop(context),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: _secondary,
                        side: const BorderSide(
                            color: Color(0xFFBDC9C6), width: 1.5),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16.r),
                        ),
                      ),
                      child: Text(
                        content.secondaryLabel!,
                        style: TextStyle(
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _onPrimaryTap(BuildContext context) {
    switch (errorType) {
      case ErrorType.noNetwork:
      case ErrorType.serverTimeout:
        // Retry → pop back to previous screen, or restart Splash if root
        if (Navigator.canPop(context)) {
          Navigator.maybePop(context);
        } else {
          Navigator.pushReplacementNamed(context, '/');
        }
        break;
      case ErrorType.sessionExpired:
        // Sign in → clear stack and go to login
        Navigator.pushNamedAndRemoveUntil(
            context, '/login', (_) => false);
    }
  }
}

class _ErrorContent {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String body;
  final String primaryLabel;
  final String? secondaryLabel;

  const _ErrorContent({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.body,
    required this.primaryLabel,
    this.secondaryLabel,
  });
}
