import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/profile_provider.dart';

class AssessmentCompleteScreen extends ConsumerStatefulWidget {
  const AssessmentCompleteScreen({super.key});

  @override
  ConsumerState<AssessmentCompleteScreen> createState() =>
      _AssessmentCompleteScreenState();
}

class _AssessmentCompleteScreenState
    extends ConsumerState<AssessmentCompleteScreen>
    with SingleTickerProviderStateMixin {
  static const Map<String, double> _demoScores = {
    'mathematics': 75.0,
    'physics': 58.0,
    'chemistry': 83.0,
    'biology': 66.0,
    'english': 91.0,
  };

  static const Map<String, String> _subjectNames = {
    'mathematics': 'Mathematics',
    'physics': 'Physics',
    'chemistry': 'Chemistry',
    'biology': 'Biology',
    'english': 'English',
  };

  static const List<String> _subjectOrder = [
    'mathematics',
    'physics',
    'chemistry',
    'biology',
    'english',
  ];

  bool _navigated = false;

  void _navigateToChat() {
    if (!mounted || _navigated) return;
    _navigated = true;
    Navigator.pushNamed(context, '/preferences');
  }

  @override
  Widget build(BuildContext context) {
    final raw = ref.watch(profileProvider).capabilityScores;
    final scores = raw.isEmpty
        ? _demoScores
        : raw.map((k, v) => MapEntry(k, (v as num).toDouble()));

    return PopScope(
      canPop: false,
      child: Scaffold(
        backgroundColor: const Color(0xFFF2F4F6),
        appBar: AppBar(
          backgroundColor: const Color(0xFFF2F4F6),
          elevation: 0,
          scrolledUnderElevation: 0,
          automaticallyImplyLeading: false,
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(20.w, 40.h, 20.w, 40.h),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // ── Profile Complete badge ──────────────────────────────────
                Container(
                  padding:
                      EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF2F4F6),
                    borderRadius: BorderRadius.circular(20.r),
                    border: Border.all(color: const Color(0xFFBDC9C6)),
                  ),
                  child: Text(
                    'PROFILE COMPLETE',
                    style: TextStyle(
                      fontSize: 9.sp,
                      fontWeight: FontWeight.w700,
                      color: const Color(0xFF515F74),
                      letterSpacing: 0.9,
                    ),
                  ),
                ),
                SizedBox(height: 24.h),

                // ── Pulsing icon ────────────────────────────────────────────
                Stack(
                  alignment: Alignment.center,
                  children: [
                    TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0.85, end: 1.15),
                      duration: const Duration(milliseconds: 1500),
                      curve: Curves.easeInOut,
                      builder: (context, scale, child) => Transform.scale(
                        scale: scale,
                        child: Container(
                          width: 120.r,
                          height: 120.r,
                          decoration: BoxDecoration(
                            color: const Color(0xFFEADDFF).withValues(alpha: 0.4),
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                      onEnd: () => setState(() {}), // re-trigger by rebuilding
                    ),
                    Container(
                      width: 96.r,
                      height: 96.r,
                      decoration: BoxDecoration(
                        color: const Color(0xFFEADDFF),
                        borderRadius: BorderRadius.circular(48.r),
                      ),
                      child: Icon(
                        Icons.auto_awesome,
                        size: 40.r,
                        color: const Color(0xFF6616D7),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 20.h),

                // ── Title ───────────────────────────────────────────────────
                Text(
                  "You're Ready",
                  style: TextStyle(
                    fontSize: 28.sp,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF191C1E),
                    letterSpacing: -0.56,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 8.h),
                Text(
                  'Your capability profile is complete. Here\'s how you performed across the five subjects.',
                  style: TextStyle(
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w400,
                    color: const Color(0xFF515F74),
                    height: 1.6,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 32.h),

                // ── Subject scores card ──────────────────────────────────────
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(20.r),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16.r),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x0F191C1E),
                        blurRadius: 24,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SUBJECT SCORES',
                        style: TextStyle(
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF515F74),
                          letterSpacing: 0.8,
                        ),
                      ),
                      SizedBox(height: 16.h),
                      ..._subjectOrder
                          .map((s) => _buildSubjectRow(s, scores[s] ?? 50.0)),
                    ],
                  ),
                ),
                SizedBox(height: 16.h),

                // ── AI insight panel ────────────────────────────────────────
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(16.r),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEADDFF),
                    borderRadius: BorderRadius.circular(16.r),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.auto_awesome,
                          size: 16.r, color: const Color(0xFF6616D7)),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: Text(
                          'Your AI career guidance is now ready. These results, combined with your interests and academic grades, will power your personalised degree recommendations.',
                          style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w400,
                            color: const Color(0xFF25005A),
                            height: 1.5,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(height: 32.h),

                // ── Auto-navigate progress bar (3 seconds → Chat) ───────────
                Semantics(
                  liveRegion: true,
                  label: 'Taking you to your results in 3 seconds',
                  child: Column(
                    children: [
                      TweenAnimationBuilder<double>(
                        tween: Tween(begin: 0.0, end: 1.0),
                        duration: const Duration(seconds: 3),
                        curve: Curves.linear,
                        onEnd: _navigateToChat,
                        builder: (context, value, child) => Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(3.r),
                              child: Container(
                                height: 6.h,
                                width: double.infinity,
                                color: const Color(0xFFF2F4F6),
                                alignment: Alignment.centerLeft,
                                child: FractionallySizedBox(
                                  widthFactor: value,
                                  child: Container(
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF006B62),
                                      borderRadius:
                                          BorderRadius.circular(3.r),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      SizedBox(height: 12.h),
                      Text(
                        'Taking you to your results…',
                        style: TextStyle(
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFF515F74),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSubjectRow(String subject, double score) {
    final isStrong = score >= 70;
    final color =
        isStrong ? const Color(0xFF006B62) : const Color(0xFF515F74);
    final name = _subjectNames[subject] ?? subject;

    return Padding(
      padding: EdgeInsets.symmetric(vertical: 10.h),
      child: Row(
        children: [
          SizedBox(
            width: 100.w,
            child: Text(
              name,
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w500,
                color: const Color(0xFF191C1E),
              ),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2.r),
              child: LinearProgressIndicator(
                value: score / 100,
                minHeight: 6.h,
                backgroundColor: const Color(0xFFE6E8EA),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
          SizedBox(width: 12.w),
          SizedBox(
            width: 40.w,
            child: Text(
              '${score.toStringAsFixed(0)}%',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w700,
                color: color,
              ),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
