import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../providers/chat_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _surfaceLow = Color(0xFFF2F4F6);
  static const Color _error = Color(0xFFBA1A1A);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);

    return Scaffold(
      backgroundColor: _surfaceLow,
      appBar: PreferredSize(
        preferredSize: Size.fromHeight(52.h),
        child: AppBar(
          backgroundColor: const Color(0xFFFFFFFF),
          elevation: 0,
          scrolledUnderElevation: 0,
          leading: IconButton(
            icon: Icon(Icons.arrow_back, size: 22.r, color: _secondary),
            onPressed: () => Navigator.pop(context),
          ),
          title: Text(
            'Settings',
            style: TextStyle(
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
              color: _onSurface,
            ),
          ),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Profile card ───────────────────────────────────────────
              _SectionCard(
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 28.r,
                        backgroundColor:
                            const Color(0xFF006B62).withValues(alpha: 0.12),
                        child: Icon(Icons.person,
                            size: 28.r, color: _primary),
                      ),
                      SizedBox(width: 16.w),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Student Account',
                              style: TextStyle(
                                fontSize: 16.sp,
                                fontWeight: FontWeight.w700,
                                color: _onSurface,
                              ),
                            ),
                            SizedBox(height: 4.h),
                            _StatusBadge(
                              label: profile.educationLevel != null
                                  ? profile.educationLevel!
                                      .replaceAll('_', ' ')
                                      .toUpperCase()
                                  : 'ONBOARDING',
                              color: _primary,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 16.h),
                  const Divider(height: 1, color: Color(0xFFE6E8EA)),
                  SizedBox(height: 12.h),
                  // Onboarding stage status
                  _LabelValue(
                    label: 'Profile Stage',
                    value: profile.onboardingStage.replaceAll('_', ' '),
                  ),
                ],
              ),

              // ── Account section ────────────────────────────────────────
              _SectionTitle(label: 'ACCOUNT'),
              SizedBox(height: 8.h),
              _SectionCard(
                children: [
                  _ActionTile(
                    id: 'settings_change_password',
                    icon: Icons.lock_outline,
                    label: 'Change Password',
                    trailing: Container(
                      padding: EdgeInsets.symmetric(
                          horizontal: 8.w, vertical: 2.h),
                      decoration: BoxDecoration(
                        color: _surfaceLow,
                        borderRadius: BorderRadius.circular(8.r),
                      ),
                      child: Text(
                        'Soon',
                        style: TextStyle(
                          fontSize: 10.sp,
                          fontWeight: FontWeight.w700,
                          color: _secondary,
                        ),
                      ),
                    ),
                    onTap: null, // Coming soon
                    color: _secondary,
                  ),
                  const Divider(height: 1, color: Color(0xFFE6E8EA)),
                  _ActionTile(
                    id: 'settings_delete_account',
                    icon: Icons.delete_outline,
                    label: 'Delete Account',
                    trailing: Container(
                      padding: EdgeInsets.symmetric(
                          horizontal: 8.w, vertical: 2.h),
                      decoration: BoxDecoration(
                        color: _surfaceLow,
                        borderRadius: BorderRadius.circular(8.r),
                      ),
                      child: Text(
                        'Soon',
                        style: TextStyle(
                          fontSize: 10.sp,
                          fontWeight: FontWeight.w700,
                          color: _secondary,
                        ),
                      ),
                    ),
                    onTap: null,
                    color: _secondary,
                  ),
                ],
              ),
              SizedBox(height: 24.h),

              // ── Sign Out button ────────────────────────────────────────
              SizedBox(
                width: double.infinity,
                height: 56.h,
                child: ElevatedButton.icon(
                  onPressed: () async {
                    final confirmed = await showDialog<bool>(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: const Text('Sign Out?'),
                        content: const Text(
                            'You will be returned to the login screen.'),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(ctx, false),
                            child: const Text('Cancel'),
                          ),
                          TextButton(
                            onPressed: () => Navigator.pop(ctx, true),
                            child: Text(
                              'Sign Out',
                              style: TextStyle(color: _error),
                            ),
                          ),
                        ],
                      ),
                    );
                    if (confirmed == true && context.mounted) {
                      await ref.read(authProvider.notifier).logout();
                      ref.read(profileProvider.notifier).reset();
                      ref.read(chatProvider.notifier).reset();
                      if (context.mounted) {
                        Navigator.pushNamedAndRemoveUntil(
                            context, '/login', (_) => false);
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFFDAD6),
                    foregroundColor: _error,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16.r),
                    ),
                  ),
                  icon: Icon(Icons.logout, size: 20.r),
                  label: Text(
                    'Sign Out',
                    style: TextStyle(
                      fontSize: 15.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
              SizedBox(height: 8.h),

              // App version
              Center(
                child: Text(
                  'Academic Intelligence · v1.0.0',
                  style: TextStyle(
                    fontSize: 11.sp,
                    color: _secondary,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
              SizedBox(height: 24.h),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Private sub-widgets ───────────────────────────────────────────────────────

class _SectionTitle extends StatelessWidget {
  final String label;
  const _SectionTitle({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(left: 4.w),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11.sp,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
          color: const Color(0xFF515F74),
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final List<Widget> children;
  const _SectionCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16.r),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 12,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.sp,
          fontWeight: FontWeight.w700,
          color: color,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _LabelValue extends StatelessWidget {
  final String label;
  final String value;
  const _LabelValue({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 13.sp,
            fontWeight: FontWeight.w400,
            color: const Color(0xFF515F74),
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 13.sp,
            fontWeight: FontWeight.w600,
            color: const Color(0xFF191C1E),
          ),
        ),
      ],
    );
  }
}


class _ActionTile extends StatelessWidget {
  final String id;
  final IconData icon;
  final String label;
  final Widget? trailing;
  final VoidCallback? onTap;
  final Color color;

  const _ActionTile({
    required this.id,
    required this.icon,
    required this.label,
    this.trailing,
    this.onTap,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      key: Key(id),
      onTap: onTap,
      borderRadius: BorderRadius.circular(12.r),
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 12.h),
        child: Row(
          children: [
            Icon(icon, size: 20.r, color: color),
            SizedBox(width: 12.w),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w500,
                  color: color,
                ),
              ),
            ),
            ?trailing,
            if (onTap != null) ...[
              SizedBox(width: 8.w),
              Icon(Icons.chevron_right, size: 18.r, color: color),
            ],
          ],
        ),
      ),
    );
  }
}


