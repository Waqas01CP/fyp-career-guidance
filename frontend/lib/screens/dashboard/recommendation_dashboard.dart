import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../models/recommendation.dart';
import '../../providers/auth_provider.dart';
import '../../providers/chat_provider.dart';
import '../../services/api_service.dart';
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

  // ── State ─────────────────────────────────────────────────────────────────
  List<Recommendation> _recommendations = [];
  String? _mismatchNotice;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRecommendations();
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final token = ref.read(authProvider).token;
    if (token == null) {
      if (mounted) {
        ref.read(authProvider.notifier).handleUnauthorized();
        Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
      }
      return;
    }

    try {
      final response =
          await ApiService.get('/recommendations', token: token);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data =
            jsonDecode(response.body) as Map<String, dynamic>;
        final recs = (data['recommendations'] as List? ?? [])
            .map((e) =>
                Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();
        final mismatch = data['mismatch_notice'] as String?;
        setState(() {
          _recommendations = recs;
          _mismatchNotice = mismatch;
          _isLoading = false;
        });
      } else if (response.statusCode == 401) {
        ref.read(authProvider.notifier).handleUnauthorized();
        Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
      } else {
        setState(() {
          _error = 'Could not load recommendations. Try again.';
          _isLoading = false;
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'No connection. Check your internet and try again.';
        _isLoading = false;
      });
    }
  }

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

  // ── Build: Empty / error state ─────────────────────────────────────────────
  Widget _buildEmptyState() {
    final hasError = _error != null;
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Semantics(
              label: hasError ? 'Error loading recommendations' : 'No recommendations yet',
              child: Icon(
                hasError ? Icons.cloud_off_outlined : Icons.school_outlined,
                // Task 5c spec: 64.r, Color(0xFF515F74)
                size: 64.r,
                color: const Color(0xFF515F74),
              ),
            ),
            SizedBox(height: 24.h),
            // Task 5f: prominent headline per screen (22-28.sp, w700)
            Text(
              hasError ? 'Could Not Load' : 'No recommendations yet',
              style: TextStyle(
                fontSize: 22.sp,
                fontWeight: FontWeight.w700,
                color: _onSurface,
                letterSpacing: -0.44,
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 10.h),
            // Task 5c spec: exact body copy for no-recs state
            Text(
              hasError
                  ? (_error ?? '')
                  : 'Start a conversation to get your personalised degree recommendations',
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
              label: hasError ? 'Try loading again' : 'Go to chat',
              button: true,
              child: SizedBox(
                width: 240.w,
                height: 52.h,
                child: ElevatedButton(
                  onPressed: hasError
                      ? _loadRecommendations
                      : () => _navigateToChat(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14.r),
                    ),
                    elevation: 0,
                  ),
                  child: Text(
                    hasError ? 'Try Again' : 'Start Chat',
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

  // ── Build: Shimmer loading skeleton ────────────────────────────────────────
  Widget _buildShimmerLoading() {
    return ListView(
      physics: const NeverScrollableScrollPhysics(),
      children: [
        SizedBox(height: 8.h),
        const _ShimmerCard(),
        const _ShimmerCard(),
        const _ShimmerCard(),
        SizedBox(height: 16.h),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
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
      body: _isLoading
          ? _buildShimmerLoading()
          : _recommendations.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  color: _primary,
                  onRefresh: _loadRecommendations,
                  child: ListView.builder(
                    physics: const BouncingScrollPhysics(),
                    itemCount:
                        _recommendations.length + (_mismatchNotice != null ? 1 : 0),
                    itemBuilder: (context, index) {
                      // Mismatch banner as first item
                      if (_mismatchNotice != null && index == 0) {
                        return _buildMismatchBanner(_mismatchNotice!);
                      }
                      final recIndex =
                          _mismatchNotice != null ? index - 1 : index;
                      final rec = _recommendations[recIndex];
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
