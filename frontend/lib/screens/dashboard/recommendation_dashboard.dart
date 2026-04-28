
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/chat_provider.dart';
import '../../widgets/university_card.dart';

class RecommendationDashboard extends ConsumerStatefulWidget {
  const RecommendationDashboard({super.key});

  @override
  ConsumerState<RecommendationDashboard> createState() =>
      _RecommendationDashboardState();
}

/// Shimmer loading placeholder — no external package required.
/// Uses a repeating AnimationController to shift a LinearGradient left-to-right
/// over placeholder shapes that match the university card skeleton.
class _ShimmerCard extends StatefulWidget {
  const _ShimmerCard();

  @override
  State<_ShimmerCard> createState() => _ShimmerCardState();
}

class _ShimmerCardState extends State<_ShimmerCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
    _anim = Tween<double>(begin: -1.0, end: 2.0).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (context, _) {
        return Container(
          margin: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 0),
          height: 160.h,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16.r),
            boxShadow: const [
              BoxShadow(
                color: Color(0x0F334155),
                blurRadius: 24,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16.r),
            child: ShaderMask(
              blendMode: BlendMode.srcATop,
              shaderCallback: (bounds) => LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                stops: const [0.0, 0.5, 1.0],
                colors: const [
                  Color(0xFFECEEF0),
                  Color(0xFFF7F9FB),
                  Color(0xFFECEEF0),
                ],
                transform: GradientRotation(_anim.value),
              ).createShader(bounds),
              child: Container(
                color: const Color(0xFFECEEF0),
                padding: EdgeInsets.all(16.r),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 40.r,
                          height: 40.r,
                          decoration: BoxDecoration(
                            color: const Color(0xFFD8DADC),
                            borderRadius: BorderRadius.circular(8.r),
                          ),
                        ),
                        SizedBox(width: 12.w),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                                width: 180.w,
                                height: 14.h,
                                color: const Color(0xFFD8DADC)),
                            SizedBox(height: 6.h),
                            Container(
                                width: 120.w,
                                height: 11.h,
                                color: const Color(0xFFD8DADC)),
                          ],
                        ),
                      ],
                    ),
                    SizedBox(height: 16.h),
                    Container(
                        width: double.infinity,
                        height: 10.h,
                        color: const Color(0xFFD8DADC)),
                    SizedBox(height: 8.h),
                    Container(
                        width: 220.w,
                        height: 10.h,
                        color: const Color(0xFFD8DADC)),
                    SizedBox(height: 16.h),
                    Row(
                      children: [
                        Container(
                            width: 70.w,
                            height: 28.h,
                            decoration: BoxDecoration(
                              color: const Color(0xFFD8DADC),
                              borderRadius: BorderRadius.circular(8.r),
                            )),
                        SizedBox(width: 8.w),
                        Container(
                            width: 70.w,
                            height: 28.h,
                            decoration: BoxDecoration(
                              color: const Color(0xFFD8DADC),
                              borderRadius: BorderRadius.circular(8.r),
                            )),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _RecommendationDashboardState
    extends ConsumerState<RecommendationDashboard> {
  // ── Colours ───────────────────────────────────────────────────────────────
  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _surface = Color(0xFFF7F9FB);

  void _navigateToChat({String? prefill}) {
    if (prefill != null) {
      ref.read(chatProvider.notifier).addUserMessage(prefill);
    }
    Navigator.pushReplacementNamed(context, '/chat');
  }

  // ── Build: Mismatch banner ─────────────────────────────────────────────────
  Widget _buildMismatchBanner(String notice) {
    return Container(
      margin: EdgeInsets.fromLTRB(16.w, 16.h, 16.w, 0),
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),
        borderRadius: BorderRadius.circular(12.r),
        border: const Border(
          left: BorderSide(color: Color(0xFFF59E0B), width: 4),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.warning_amber_rounded,
              color: Color(0xFFB45309), size: 18),
          SizedBox(width: 10.w),
          Expanded(
            child: Text(
              notice,
              style: TextStyle(
                fontSize: 13.sp,
                fontWeight: FontWeight.w400,
                color: _onSurface,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Build: Empty state ─────────────────────────────────────────────────────
  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Semantics(
              label: 'No recommendations yet',
              child: Icon(
                Icons.school_outlined,
                size: 64.r,
                color: const Color(0xFF515F74),
              ),
            ),
            SizedBox(height: 24.h),
            Text(
              'No recommendations yet',
              style: TextStyle(
                fontSize: 22.sp,
                fontWeight: FontWeight.w700,
                color: _onSurface,
                letterSpacing: -0.44,
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 10.h),
            Text(
              'Start a conversation to get your personalised degree recommendations',
              style: TextStyle(
                fontSize: 15.sp,
                fontWeight: FontWeight.w400,
                color: _secondary,
                height: 1.65,
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 32.h),
            Semantics(
              label: 'Go to chat',
              button: true,
              child: SizedBox(
                width: 240.w,
                height: 52.h,
                child: ElevatedButton(
                  onPressed: () => _navigateToChat(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14.r),
                    ),
                    elevation: 0,
                  ),
                  child: Text(
                    'Start Chat',
                    style: TextStyle(
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }



  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);
    final recommendations = chatState.recommendations;
    final timelineData = chatState.roadmapTimeline;
    final mismatchNotice = timelineData?['mismatch_notice'] as String?;

    return Scaffold(
      backgroundColor: _surface,
      appBar: PreferredSize(
        preferredSize: Size.fromHeight(52.h),
        child: AppBar(
          backgroundColor: _primary,
          elevation: 0,
          automaticallyImplyLeading: false,
          title: Text(
            'Recommendations',
            style: TextStyle(
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          actions: [
            IconButton(
              icon: Icon(Icons.chat_bubble_outline,
                  color: Colors.white, size: 22.r),
              onPressed: () => _navigateToChat(),
              tooltip: 'Chat',
            ),
            IconButton(
              icon: Icon(Icons.settings_outlined,
                  color: Colors.white, size: 22.r),
              onPressed: () => Navigator.pushNamed(context, '/settings'),
              tooltip: 'Settings',
            ),
            SizedBox(width: 4.w),
          ],
        ),
      ),
      body: recommendations.isEmpty
          ? _buildEmptyState()
          : ListView.builder(
              physics: const BouncingScrollPhysics(),
              itemCount:
                  recommendations.length + (mismatchNotice != null ? 1 : 0),
              itemBuilder: (context, index) {
                // Mismatch banner as first item
                if (mismatchNotice != null && index == 0) {
                  return _buildMismatchBanner(mismatchNotice);
                }
                final recIndex =
                    mismatchNotice != null ? index - 1 : index;
                final rec = recommendations[recIndex];
                return UniversityCard(
                  recommendation: rec,
                  onAskAbout: () => _navigateToChat(
                    prefill:
                        'Tell me more about ${rec.universityName} — ${rec.degreeName}',
                  ),
                  onMoreDetails: () => _navigateToChat(
                    prefill:
                        'Give me detailed information about ${rec.universityName} ${rec.degreeName}, including admission requirements and fees.',
                  ),
                );
              },
            ),
      // ── Bottom padding for last card ─────────────────────────────────────
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: Colors.white,
        selectedItemColor: _primary,
        unselectedItemColor: _secondary,
        selectedLabelStyle: TextStyle(
          fontSize: 11.sp,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelStyle: TextStyle(
          fontSize: 11.sp,
          fontWeight: FontWeight.w600,
        ),
        currentIndex: 1,
        elevation: 16,
        onTap: (index) {
          switch (index) {
            case 0:
              Navigator.pushReplacementNamed(context, '/chat');
            case 1:
              // Already on dashboard
              break;
            case 2:
              Navigator.pushNamed(context, '/settings');
          }
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_bubble_outline),
            activeIcon: Icon(Icons.chat_bubble),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard_outlined),
            activeIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings_outlined),
            activeIcon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}
