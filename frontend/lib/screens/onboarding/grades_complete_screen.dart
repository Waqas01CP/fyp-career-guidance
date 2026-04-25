import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/profile_provider.dart';

class GradesCompleteScreen extends ConsumerWidget {
  const GradesCompleteScreen({super.key});

  static const Map<String, double> _demoMarks = {
    'Mathematics':      85.0,
    'Physics':          78.0,
    'Chemistry':        82.0,
    'English':          68.0,
    'Computer Science': 91.0,
  };

  String _formatEducationLevel(String? level) {
    switch (level) {
      case 'matric':          return 'Matric';
      case 'inter_part1':     return 'Inter Part 1';
      case 'inter_part2':     return 'Inter Part 2';
      case 'completed_inter': return 'Completed Inter';
      case 'o_level':         return 'O Level';
      case 'a_level':         return 'A Level';
      default:                return 'Inter';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    final raw = profile.subjectMarks;

    // Correction 2: title-case the lowercase keys from profileProvider
    final Map<String, double> marks = raw.isEmpty
        ? _demoMarks
        : {
            for (final e in raw.entries)
              '${e.key[0].toUpperCase()}${e.key.substring(1)}':
                  (e.value as num).toDouble()
          };

    final aggregate = marks.values.isEmpty
        ? 0.0
        : marks.values.reduce((a, b) => a + b) / marks.length;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FB),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF7F9FB),
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: const Color(0xFF515F74), size: 24.r),
          onPressed: () => Navigator.maybePop(context),
        ),
        title: Text(
          'Academic Profile',
          style: TextStyle(
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
            color: const Color(0xFF191C1E),
          ),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(20.w, 24.h, 20.w, 40.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Hero block ──────────────────────────────────
              Column(
                children: [
                  // Icon circle
                  Container(
                    width: 80.w,
                    height: 80.h,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [Color(0xFF006B62), Color(0xFF00857A)],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0x4C006B62),
                          blurRadius: 32,
                          offset: const Offset(0, 12),
                        ),
                      ],
                    ),
                    child: Icon(Icons.school,
                        size: 40.r, color: Colors.white),
                  ),
                  SizedBox(height: 20.h),

                  // Step badge
                  Container(
                    padding: EdgeInsets.symmetric(
                        horizontal: 14.w, vertical: 4.h),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF2F4F6),
                      borderRadius: BorderRadius.circular(20.r),
                    ),
                    child: Text(
                      'STEP 2 OF 3 COMPLETE',
                      style: TextStyle(
                        fontSize: 9.sp,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.1 * 9,
                        color: const Color(0xFF515F74),
                      ),
                    ),
                  ),
                  SizedBox(height: 16.h),

                  // Title
                  Text(
                    'Academic Grades\nCaptured',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 28.sp,
                      fontWeight: FontWeight.w700,
                      color: const Color(0xFF191C1E),
                      letterSpacing: -0.02 * 28,
                      height: 1.2,
                    ),
                  ),
                  SizedBox(height: 10.h),

                  // Subtitle
                  Text(
                    'Your marks have been saved. These will be used to calculate eligibility at each university.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 15.sp,
                      fontWeight: FontWeight.w400,
                      color: const Color(0xFF515F74),
                      height: 1.6,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 32.h),

              // ── Grades summary card ─────────────────────────
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20.r),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x0F334155),
                      blurRadius: 40,
                      offset: Offset(0, 12),
                    ),
                  ],
                ),
                padding: EdgeInsets.all(24.r),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Card header
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'MARKS SUMMARY',
                          style: TextStyle(
                            fontSize: 10.sp,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.1 * 10,
                            color: const Color(0xFF515F74),
                          ),
                        ),
                        Container(
                          padding: EdgeInsets.symmetric(
                              horizontal: 10.w, vertical: 3.h),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF2F4F6),
                            borderRadius: BorderRadius.circular(20.r),
                          ),
                          child: Text(
                            _formatEducationLevel(profile.educationLevel),
                            style: TextStyle(
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w600,
                              color: const Color(0xFF515F74),
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 20.h),

                    // Subject rows
                    ...marks.entries.toList().asMap().entries.map((entry) {
                      final i = entry.key;
                      final subject = entry.value.key;
                      final pct     = entry.value.value;
                      final isLast  = i == marks.length - 1;
                      return Column(
                        children: [
                          _buildSubjectRow(subject, pct),
                          if (!isLast)
                            Container(
                              height: 1,
                              color: const Color(0xFFF2F4F6),
                            ),
                        ],
                      );
                    }),

                    // Aggregate row (gradient separator)
                    Container(
                      margin: EdgeInsets.only(top: 16.h),
                      padding: EdgeInsets.only(top: 16.h),
                      decoration: const BoxDecoration(
                        border: Border(
                          top: BorderSide(
                            color: Color(0xFFF2F4F6),
                            width: 1,
                          ),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Overall Aggregate',
                            style: TextStyle(
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w600,
                              color: const Color(0xFF515F74),
                            ),
                          ),
                          Text(
                            '${aggregate.toStringAsFixed(0)}%',
                            style: TextStyle(
                              fontSize: 22.sp,
                              fontWeight: FontWeight.w800,
                              color: const Color(0xFF006B62),
                              letterSpacing: -0.02 * 22,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 20.h),

              // ── AI Insight panel ────────────────────────────
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFEADDFF),
                  borderRadius: BorderRadius.circular(16.r),
                  border: const Border(
                    left: BorderSide(color: Color(0xFF6616D7), width: 4),
                  ),
                ),
                padding: EdgeInsets.all(16.r),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.auto_awesome,
                            size: 14.r, color: const Color(0xFF6616D7)),
                        SizedBox(width: 6.w),
                        Text(
                          'AI INSIGHT',
                          style: TextStyle(
                            fontSize: 9.sp,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.1 * 9,
                            color: const Color(0xFF5A00C6),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 8.h),
                    Text(
                      'Your grades have been captured. '
                      'Strong performance in technical subjects '
                      'supports engineering and CS pathways.',
                      style: TextStyle(
                        fontSize: 13.sp,
                        fontWeight: FontWeight.w400,
                        color: const Color(0xFF25005A),
                        height: 1.6,
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 32.h),

              // ── Continue button ─────────────────────────────
              ElevatedButton(
                onPressed: () =>
                    Navigator.pushReplacementNamed(context, '/assessment'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF006B62),
                  minimumSize: Size(double.infinity, 56.h),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16.r),
                  ),
                  padding: EdgeInsets.all(18.r),
                  shadowColor: const Color(0x40006B62),
                  elevation: 8,
                ),
                child: Text(
                  'Continue to Capability Assessment',
                  style: TextStyle(
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSubjectRow(String subject, double percentage) {
    final isHigh  = percentage >= 70;
    final barColor = isHigh
        ? const Color(0xFF006B62)
        : const Color(0xFF515F74);

    return Padding(
      padding: EdgeInsets.symmetric(vertical: 12.h),
      child: Row(
        children: [
          Expanded(
            child: Text(
              subject,
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w500,
                color: const Color(0xFF191C1E),
              ),
            ),
          ),
          SizedBox(
            width: 80.w,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2.r),
              child: LinearProgressIndicator(
                value: percentage / 100,
                minHeight: 4.h,
                backgroundColor: const Color(0xFFE6E8EA),
                valueColor: AlwaysStoppedAnimation<Color>(barColor),
              ),
            ),
          ),
          SizedBox(width: 12.w),
          Text(
            '${percentage.toStringAsFixed(0)}%',
            style: TextStyle(
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
              color: barColor,
            ),
          ),
        ],
      ),
    );
  }
}
