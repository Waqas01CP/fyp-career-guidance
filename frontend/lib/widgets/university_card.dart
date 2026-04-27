import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../models/recommendation.dart';

/// UniversityCard — full card per DESIGN_HANDOFF Screen 13 spec.
/// Displays a single [Recommendation] with rank badge, match score bar,
/// merit tier badge, FutureValue badge, AI flags row, and action buttons.
class UniversityCard extends StatelessWidget {
  final Recommendation recommendation;
  final VoidCallback? onAskAbout;
  final VoidCallback? onMoreDetails;

  const UniversityCard({
    super.key,
    required this.recommendation,
    this.onAskAbout,
    this.onMoreDetails,
  });

  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _tertiary = Color(0xFF6616D7);
  static const Color _tertiaryFixed = Color(0xFFEADDFF);
  static const Color _surfaceLowest = Color(0xFFFFFFFF);
  static const Color _surfaceHigh = Color(0xFFE6E8EA);

  Color _meritColor(String tier) {
    switch (tier.toLowerCase()) {
      case 'high merit':
      case 'high':
        return const Color(0xFF10B981);
      case 'good match':
      case 'medium':
        return const Color(0xFFF59E0B);
      default:
        return const Color(0xFFEF4444);
    }
  }

  /// Convert lifecycle_status to display label for FutureValue badge.
  String _futureValueLabel(String status) {
    switch (status.toLowerCase()) {
      case 'emerging':
        return 'Emerging';
      case 'peak':
        return 'Peak Demand';
      case 'saturated':
        return 'Saturated';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final rec = recommendation;
    final meritColor = _meritColor(rec.meritTier);
    final matchPct = rec.matchScoreNormalised * 100;
    final futureLabel = _futureValueLabel(rec.lifecycleStatus);
    final showFuture = rec.lifecycleStatus.isNotEmpty;

    return Container(
      margin: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 0),
      decoration: BoxDecoration(
        color: _surfaceLowest,
        borderRadius: BorderRadius.circular(16.r),
        // Task 5d: standardized content card shadow token
        boxShadow: const [
          BoxShadow(
            color: Color(0x0F334155),
            blurRadius: 24,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Padding(
        padding: EdgeInsets.all(20.r),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header: rank badge + names ──────────────────────────────
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 32.r,
                  height: 32.r,
                  decoration: BoxDecoration(
                    color: _primary,
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    '#${rec.rank}',
                    style: TextStyle(
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ),
                SizedBox(width: 12.w),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        rec.universityName,
                        style: TextStyle(
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w700,
                          color: _onSurface,
                        ),
                      ),
                      SizedBox(height: 2.h),
                      Text(
                        rec.degreeName,
                        style: TextStyle(
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w400,
                          color: _secondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            SizedBox(height: 16.h),

            // ── Match score bar ─────────────────────────────────────────
            Row(
              children: [
                Text(
                  'Match',
                  style: TextStyle(
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w500,
                    color: _secondary,
                  ),
                ),
                SizedBox(width: 8.w),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(3.r),
                    child: LinearProgressIndicator(
                      value: rec.matchScoreNormalised.clamp(0.0, 1.0),
                      minHeight: 6.h,
                      backgroundColor: _surfaceHigh,
                      valueColor:
                          const AlwaysStoppedAnimation<Color>(_primary),
                    ),
                  ),
                ),
                SizedBox(width: 8.w),
                Text(
                  '${matchPct.toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w700,
                    color: _primary,
                  ),
                ),
              ],
            ),
            SizedBox(height: 12.h),

            // ── Badges row ──────────────────────────────────────────────
            Wrap(
              spacing: 8.w,
              runSpacing: 6.h,
              children: [
                // Merit tier
                Container(
                  padding:
                      EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: meritColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20.r),
                  ),
                  child: Text(
                    rec.meritTier.toUpperCase(),
                    style: TextStyle(
                      fontSize: 10.sp,
                      fontWeight: FontWeight.w700,
                      color: meritColor,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                // FutureValue badge (AI purple — lifecycle_status)
                if (showFuture)
                  Container(
                    padding:
                        EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
                    decoration: BoxDecoration(
                      color: _tertiaryFixed,
                      borderRadius: BorderRadius.circular(20.r),
                      border: Border.all(color: _tertiary, width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.auto_awesome,
                            size: 11.r, color: _tertiary),
                        SizedBox(width: 4.w),
                        Text(
                          futureLabel.toUpperCase(),
                          style: TextStyle(
                            fontSize: 10.sp,
                            fontWeight: FontWeight.w700,
                            color: _tertiary,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                // Policy pending flag
                if (rec.policyPendingVerification)
                  Container(
                    padding:
                        EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(20.r),
                      border: Border.all(
                          color: const Color(0xFFF59E0B), width: 1),
                    ),
                    child: Text(
                      'POLICY PENDING',
                      style: TextStyle(
                        fontSize: 10.sp,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFFB45309),
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
              ],
            ),

            // ── AI soft-flags row ────────────────────────────────────────
            if (rec.softFlags.isNotEmpty) ...[
              SizedBox(height: 10.h),
              Wrap(
                spacing: 6.w,
                runSpacing: 6.h,
                children: rec.softFlags
                    .map((flag) => Container(
                          padding: EdgeInsets.symmetric(
                              horizontal: 8.w, vertical: 3.h),
                          decoration: BoxDecoration(
                            color: _tertiaryFixed,
                            borderRadius: BorderRadius.circular(12.r),
                          ),
                          child: Text(
                            flag,
                            style: TextStyle(
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w600,
                              color: _tertiary,
                            ),
                          ),
                        ))
                    .toList(),
              ),
            ],

            // ── Fee display ──────────────────────────────────────────────
            if (rec.feePerSemester > 0) ...[
              SizedBox(height: 10.h),
              Text(
                'Fee: PKR ${_formatFee(rec.feePerSemester)}/semester',
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w500,
                  color: _secondary,
                ),
              ),
            ],

            // ── Divider + actions ────────────────────────────────────────
            SizedBox(height: 12.h),
            Divider(
              height: 1,
              color: const Color(0xFFBDC9C6).withValues(alpha: 0.15),
            ),
            SizedBox(height: 4.h),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                TextButton.icon(
                  onPressed: onAskAbout,
                  icon: Icon(Icons.chat_bubble_outline,
                      size: 16.r, color: _primary),
                  label: Text(
                    'Ask about this',
                    style: TextStyle(
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w600,
                      color: _primary,
                    ),
                  ),
                  style: TextButton.styleFrom(
                    padding: EdgeInsets.symmetric(
                        horizontal: 8.w, vertical: 6.h),
                  ),
                ),
                TextButton(
                  onPressed: onMoreDetails,
                  style: TextButton.styleFrom(
                    padding: EdgeInsets.symmetric(
                        horizontal: 8.w, vertical: 6.h),
                  ),
                  child: Text(
                    'More Details',
                    style: TextStyle(
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w600,
                      color: _secondary,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatFee(double fee) {
    if (fee >= 100000) {
      return '${(fee / 1000).toStringAsFixed(0)}K';
    }
    return fee.toStringAsFixed(0);
  }
}
