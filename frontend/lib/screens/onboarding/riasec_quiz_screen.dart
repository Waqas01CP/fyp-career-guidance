import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/api_service.dart';

class RiasecQuizScreen extends ConsumerStatefulWidget {
  const RiasecQuizScreen({super.key});

  @override
  ConsumerState<RiasecQuizScreen> createState() => _RiasecQuizScreenState();
}

class _RiasecQuizScreenState extends ConsumerState<RiasecQuizScreen>
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  static const Color _primary           = Color(0xFF006B62);
  static const Color _secondary         = Color(0xFF515F74);
  static const Color _onSurface         = Color(0xFF191C1E);
  static const Color _tertiary          = Color(0xFF6616D7);
  static const Color _tertiaryFixed     = Color(0xFFEADDFF);
  static const Color _onTertiaryFixedVar = Color(0xFF5A00C6);
  static const Color _onTertiaryFixed   = Color(0xFF25005A);
  static const Color _unselected        = Color(0xFFE6E8EA);

  static const Map<String, String> _dimensionNames = {
    'R': 'Realistic',
    'I': 'Investigative',
    'A': 'Artistic',
    'S': 'Social',
    'E': 'Enterprising',
    'C': 'Conventional',
  };

  // Verbatim from code_riasec_quiz.html AI insight panel.
  // HTML provides general RIASEC text for R/I/A/S/E and one
  // dimension-specific observation for C only.
  static const Map<String, String> _dimensionInsights = {
    'R': 'The RIASEC model measures six personality types: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. Answer based on how much you\'d genuinely enjoy each activity — not what you think you should say.',
    'I': 'The RIASEC model measures six personality types: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. Answer based on how much you\'d genuinely enjoy each activity — not what you think you should say.',
    'A': 'The RIASEC model measures six personality types: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. Answer based on how much you\'d genuinely enjoy each activity — not what you think you should say.',
    'S': 'The RIASEC model measures six personality types: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. Answer based on how much you\'d genuinely enjoy each activity — not what you think you should say.',
    'E': 'The RIASEC model measures six personality types: Realistic, Investigative, Artistic, Social, Enterprising, and Conventional. Answer based on how much you\'d genuinely enjoy each activity — not what you think you should say.',
    'C': 'You\'re showing a strong Conventional pattern — your answers suggest you may thrive in structured, data-driven environments like Accounting, Finance, or Business Administration in Karachi.',
  };

  List<Map<String, dynamic>> _questions = [];
  Map<String, String> _scaleLabels = const {};
  int _currentIndex = 0;
  final Map<int, int> _answers = {};
  int? _selectedAnswer;
  bool _isSubmitting = false;
  bool _isGoingForward = true;
  bool _showRomanUrdu = false;

  final _storage = const FlutterSecureStorage();
  Timer? _saveTimer;
  // NOTE: No _userId field — draft key uses sessionId from profileProvider.
  // sessionId is a stable UUID per user account (GET /profile/me → session_id).
  // This survives logout/login because it's tied to the account, not the JWT.

  late final AnimationController _animController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _initQuiz();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _saveTimer?.cancel();
    _animController.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      _saveTimer?.cancel();
      _saveDraft();
    }
  }

  /// Returns a stable storage key for this user's RIASEC draft.
  ///
  /// Primary: sessionId (stable UUID per user account — survives logout/login).
  /// Fallback: token.hashCode (stable within a single login session).
  /// Last resort: 'anonymous' (prevents crash; draft won't persist across logins).
  String _draftKey() {
    final sessionId = ref.read(profileProvider).sessionId;
    if (sessionId != null) return 'draft_riasec_$sessionId';
    // Fallback: token hash — better than a shared key, worse than sessionId
    final token = ref.read(authProvider).token;
    return token != null
        ? 'draft_riasec_${token.hashCode}'
        : 'draft_riasec_anonymous';
  }

  Future<void> _saveDraft() async {
    try {
      final draft = jsonEncode({
        'currentIndex': _currentIndex,
        'answers': _answers.map((k, v) => MapEntry(k.toString(), v)),
      });
      await _storage.write(key: _draftKey(), value: draft);
    } catch (e) {
      debugPrint('Draft save failed: $e');
    }
  }

  Future<void> _loadDraft() async {
    try {
      final stored = await _storage.read(key: _draftKey());
      if (stored == null) return;

      final data = jsonDecode(stored) as Map<String, dynamic>;
      final savedIndex = data['currentIndex'] as int? ?? 0;
      final savedAnswers =
          (data['answers'] as Map<String, dynamic>? ?? {})
              .map((k, v) => MapEntry(int.parse(k), v as int));

      if (_questions.isEmpty) return;
      if (savedIndex >= _questions.length) return;

      if (mounted) {
        setState(() {
          _currentIndex = savedIndex;
          _answers.clear();
          _answers.addAll(savedAnswers);
          _selectedAnswer = _answers[_questions[savedIndex]['id'] as int];
        });
      }
    } catch (e) {
      debugPrint('Draft restore failed: $e — clearing draft');
      await _clearDraft();
    }
  }

  Future<void> _clearDraft() async {
    try {
      await _storage.delete(key: _draftKey());
    } catch (e) {
      debugPrint('Draft clear failed: $e');
    }
  }

  void _scheduleDraftSave() {
    _saveTimer?.cancel();
    _saveTimer = Timer(const Duration(milliseconds: 500), _saveDraft);
  }

  Future<void> _initQuiz() async {
    // sessionId is already in profileProvider if splash loaded the profile.
    // If not (edge case: direct navigation), it will be populated after quiz init.
    // _draftKey() reads from profileProvider at call time — always current.

    final stage = ref.read(profileProvider).onboardingStage;
    const completedStages = [
      'riasec_complete',
      'grades_complete',
      'assessment_complete',
    ];
    if (completedStages.contains(stage)) {
      await _clearDraft();
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/grades-input');
      }
      return;
    }

    await _loadQuestions();
    await _loadDraft();
  }

  Future<void> _loadQuestions() async {
    final jsonStr =
        await rootBundle.loadString('assets/riasec_questions.json');
    final data = jsonDecode(jsonStr) as Map<String, dynamic>;
    final qs = (data['questions'] as List).cast<Map<String, dynamic>>();
    final rawLabels =
        data['meta']['scale_labels'] as Map<String, dynamic>;
    final labels = <String, String>{};
    rawLabels.forEach((key, val) {
      labels[key] = (val as Map<String, dynamic>)['en'] as String;
    });
    if (mounted) {
      setState(() {
        _questions = qs;
        _scaleLabels = labels;
      });
    }
  }

  Future<void> _onBackPressed() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Leave quiz?'),
        content: const Text(
            'Your progress has been saved automatically and will be restored when you return.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Stay'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text(
              'Leave',
              style: TextStyle(color: Color(0xFFBA1A1A)),
            ),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.of(context, rootNavigator: true)
            .pushNamedAndRemoveUntil('/login', (route) => false);
      });
    }
  }

  void _onNext() {
    if (_selectedAnswer == null || _questions.isEmpty) return;
    _answers[_questions[_currentIndex]['id'] as int] = _selectedAnswer!;
    setState(() {
      _isGoingForward = true;
      _currentIndex++;
      _selectedAnswer =
          _answers[_questions[_currentIndex]['id'] as int];
    });
    _scheduleDraftSave();
  }

  void _onPrevious() {
    if (_currentIndex <= 0) return;
    if (_selectedAnswer != null) {
      _answers[_questions[_currentIndex]['id'] as int] =
          _selectedAnswer!;
    }
    setState(() {
      _isGoingForward = false;
      _currentIndex--;
      _selectedAnswer =
          _answers[_questions[_currentIndex]['id'] as int];
    });
    _scheduleDraftSave();
  }

  Future<void> _onSubmit() async {
    if (_selectedAnswer == null) return;
    _answers[_questions[_currentIndex]['id'] as int] = _selectedAnswer!;
    setState(() => _isSubmitting = true);

    final token = ref.read(authProvider).token;
    if (token == null) {
      setState(() => _isSubmitting = false);
      return;
    }

    // Aggregate 60 individual answers into 6 dimension sums (10–50 range).
    // Backend expects: {'responses': {'R': int, 'I': int, ...}}
    final Map<String, int> dimensionTotals = {
      'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0,
    };
    for (final q in _questions) {
      final id  = q['id'] as int;
      final dim = q['dimension'] as String;
      final score = _answers[id] ?? 3;
      dimensionTotals[dim] = (dimensionTotals[dim] ?? 0) + score;
    }

    try {
      final response = await ApiService.post(
        '/profile/quiz',
        {'responses': dimensionTotals},
        token: token,
      );
      if (response.statusCode == 200) {
        await _clearDraft();
        await ref.read(profileProvider.notifier).loadProfile(token);
        if (!mounted) return;
        Navigator.pushNamed(context, '/riasec-complete');
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Submission failed. Try again.'),
            backgroundColor: Color(0xFFBA1A1A),
          ),
        );
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No connection. Check your internet.'),
          backgroundColor: Color(0xFFBA1A1A),
        ),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Widget _buildLikertButton(int score, String label, bool isSelected) {
    return InkWell(
      onTap: () {
        final qId = _questions[_currentIndex]['id'] as int;
        setState(() {
          _selectedAnswer = score;
          _answers[qId] = score;
        });
        _scheduleDraftSave();
      },
      borderRadius: BorderRadius.circular(12.r),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: double.infinity,
        height: 52.h,
        decoration: BoxDecoration(
          color: isSelected ? _primary : _unselected,
          borderRadius: BorderRadius.circular(12.r),
        ),
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(horizontal: 2.w),
        child: Text(
          label.toUpperCase(),
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 14.sp,
            fontWeight: FontWeight.w600,
            color: isSelected ? Colors.white : _secondary,
            letterSpacing: 0.02,
          ),
        ),
      ),
    );
  }

  Widget _buildInsightPanel(String insightText) {
    return Container(
      margin: EdgeInsets.only(top: 20.h),
      decoration: BoxDecoration(
        color: _tertiaryFixed,
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          dividerColor: Colors.transparent,
        ),
        child: ExpansionTile(
          initiallyExpanded: false,
          tilePadding: EdgeInsets.zero,
          childrenPadding: EdgeInsets.zero,
          leading: Icon(Icons.info_outline,
              size: 18.r, color: _tertiary),
          title: Text('GUIDANCE',
              style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w700,
                  color: _onTertiaryFixedVar,
                  letterSpacing: 1.0)),
          iconColor: _tertiary,
          collapsedIconColor: _tertiary,
          backgroundColor: _tertiaryFixed,
          collapsedBackgroundColor: _tertiaryFixed,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16.r)),
          collapsedShape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16.r)),
          children: [
            Padding(
              padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 16.h),
              child: Text(insightText,
                  style: TextStyle(
                      fontSize: 14.sp,
                      color: _onTertiaryFixed,
                      height: 1.6)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionCard({required Key key}) {
    final q = _questions[_currentIndex];
    final dimension = q['dimension'] as String;
    final textEn    = q['text_en'] as String;
    final textUr    = q['text_ur'] as String?;
    final dimName   = _dimensionNames[dimension] ?? dimension;
    final insight   = _dimensionInsights[dimension];

    return Container(
      key: key,
      margin: EdgeInsets.fromLTRB(16.w, 16.h, 16.w, 16.h),
      padding: EdgeInsets.all(24.r),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: EdgeInsets.symmetric(
                    horizontal: 12.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F4F6),
                  borderRadius: BorderRadius.circular(20.r),
                ),
                child: Text(
                  dimName.toUpperCase(),
                  style: TextStyle(
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w700,
                    color: _primary,
                    letterSpacing: 0.06,
                  ),
                ),
              ),
              GestureDetector(
                onTap: _showQuestionPicker,
                child: Container(
                  padding: EdgeInsets.symmetric(
                      horizontal: 12.w, vertical: 6.h),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF2F4F6),
                    borderRadius: BorderRadius.circular(20.r),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Q${_currentIndex + 1} OF ${_questions.length}',
                        style: TextStyle(
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF515F74),
                          letterSpacing: 0.88,
                        ),
                      ),
                      SizedBox(width: 4.w),
                      Icon(Icons.keyboard_arrow_down,
                          size: 14.r, color: const Color(0xFF515F74)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 20.h),
          Text(
            _showRomanUrdu ? (textUr ?? textEn) : textEn,
            style: TextStyle(
              fontSize: 18.sp,
              fontWeight: FontWeight.w500,
              color: _onSurface,
              height: 1.6,
            ),
          ),
          SizedBox(height: 24.h),
          Column(
            children: [
              for (int i = 1; i <= 5; i++) ...[
                _buildLikertButton(
                  i,
                  _scaleLabels['$i'] ?? '$i',
                  _selectedAnswer == i,
                ),
                if (i < 5) SizedBox(height: 8.h),
              ],
            ],
          ),
          if (insight != null) _buildInsightPanel(insight),
        ],
      ),
    );
  }

  Widget _buildAppBar() {
    return Container(
      height: 52.h,
      padding: EdgeInsets.symmetric(horizontal: 8.w),
      color: const Color(0xFFF7F9FB),
      child: Row(
        children: [
          SizedBox(
            width: 48.w,
            height: 48.h,
            child: InkWell(
              onTap: _onBackPressed,
              borderRadius: BorderRadius.circular(8.r),
              child: Icon(
                Icons.arrow_back,
                color: _secondary,
                size: 24.r,
              ),
            ),
          ),
          SizedBox(width: 4.w),
          Icon(Icons.school, color: _primary, size: 22.r),
          const Spacer(),
          TextButton(
            onPressed: () =>
                setState(() => _showRomanUrdu = !_showRomanUrdu),
            child: Text(
              _showRomanUrdu ? 'EN' : 'UR',
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF006B62),
              ),
            ),
          ),
          Text(
            'Step 1 of 3',
            style: TextStyle(
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              color: _secondary,
            ),
          ),
          SizedBox(width: 10.w),
          Container(
            width: 32.w,
            height: 32.h,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: _unselected,
            ),
            child: Icon(Icons.person, size: 16.r, color: _secondary),
          ),
          SizedBox(width: 8.w),
        ],
      ),
    );
  }

  Widget _buildNavRow() {
    final isLast         = _currentIndex == _questions.length - 1;
    final isPrevDisabled = _currentIndex <= 0;
    final unansweredCount = _questions.length - _answers.length;
    final allAnswered     = unansweredCount == 0;
    final isSubmitEnabled = _selectedAnswer != null && !_isSubmitting && allAnswered;

    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 16.h),
      decoration: const BoxDecoration(
        color: Color(0xFFF7F9FB),
        border: Border(
          top: BorderSide(color: Color(0x33BDC9C6), width: 1),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          TextButton.icon(
            onPressed: isPrevDisabled ? null : _onPrevious,
            icon: Icon(Icons.arrow_back, size: 18.r),
            label: const Text('Previous'),
            style: TextButton.styleFrom(
              foregroundColor: _secondary,
              disabledForegroundColor: const Color(0xFFBDC9C6),
              padding: EdgeInsets.symmetric(
                  horizontal: 16.w, vertical: 14.h),
              textStyle: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          if (isLast)
            _buildViewResultsButton(isSubmitEnabled, unansweredCount)
          else
            ElevatedButton.icon(
              onPressed: _selectedAnswer == null ? null : _onNext,
              icon: const Text('Next'),
              label: Icon(Icons.arrow_forward, size: 18.r),
              style: ElevatedButton.styleFrom(
                backgroundColor: _primary,
                disabledBackgroundColor: const Color(0xFFE0E3E5),
                foregroundColor: Colors.white,
                disabledForegroundColor: const Color(0xFF6E7977),
                padding: EdgeInsets.symmetric(
                    horizontal: 24.w, vertical: 14.h),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12.r),
                ),
                elevation: 0,
                textStyle: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildViewResultsButton(bool isEnabled, int unansweredCount) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isEnabled ? _onSubmit : null,
        borderRadius: BorderRadius.circular(14.r),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          height: 52.h,
          decoration: BoxDecoration(
            gradient: isEnabled
                ? const LinearGradient(
                    colors: [Color(0xFF6616D7), Color(0xFF7F3EF0)],
                  )
                : null,
            color: isEnabled ? null : const Color(0xFFE0E3E5),
            borderRadius: BorderRadius.circular(14.r),
          ),
          alignment: Alignment.center,
          padding: EdgeInsets.symmetric(horizontal: 24.w),
          child: _isSubmitting
              ? SizedBox(
                  height: 20.r,
                  width: 20.r,
                  child: const CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(
                  unansweredCount > 0
                      ? '$unansweredCount left to answer'
                      : 'View My Results',
                  style: TextStyle(
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w700,
                    color: isEnabled
                        ? Colors.white
                        : const Color(0xFF6E7977),
                  ),
                ),
        ),
      ),
    );
  }

  void _showQuestionPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(
          borderRadius:
              BorderRadius.vertical(top: Radius.circular(24.r))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.all(24.r),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Jump to Question',
                style: TextStyle(
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF191C1E))),
            SizedBox(height: 16.h),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate:
                  const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 10,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
                childAspectRatio: 1,
              ),
              itemCount: _questions.length,
              itemBuilder: (ctx, i) {
                final isAnswered = _answers.containsKey(
                    _questions[i]['id'] as int);
                final isCurrent = i == _currentIndex;
                return GestureDetector(
                  onTap: () {
                    if (_selectedAnswer != null) {
                      _answers[_questions[_currentIndex]['id']
                          as int] = _selectedAnswer!;
                    }
                    setState(() {
                      _isGoingForward = i > _currentIndex;
                      _currentIndex = i;
                      _selectedAnswer =
                          _answers[_questions[i]['id'] as int];
                    });
                    _scheduleDraftSave();
                    Navigator.pop(ctx);
                  },
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isAnswered
                          ? const Color(0xFF006B62)
                          : const Color(0xFFE6E8EA),
                      border: isCurrent
                          ? Border.all(
                              color: const Color(0xFF006B62),
                              width: 2)
                          : null,
                    ),
                    alignment: Alignment.center,
                    child: Text('${i + 1}',
                        style: TextStyle(
                            fontSize: 10.sp,
                            fontWeight: FontWeight.w600,
                            color: isAnswered
                                ? Colors.white
                                : const Color(0xFF515F74))),
                  ),
                );
              },
            ),
            SizedBox(height: 8.h),
            Row(
              children: [
                _buildLegendDot(const Color(0xFF006B62)),
                SizedBox(width: 6.w),
                Text('Answered',
                    style: TextStyle(
                        fontSize: 13.sp, color: const Color(0xFF515F74))),
                SizedBox(width: 16.w),
                _buildLegendDot(const Color(0xFFE6E8EA)),
                SizedBox(width: 6.w),
                Text('Unanswered',
                    style: TextStyle(
                        fontSize: 13.sp, color: const Color(0xFF515F74))),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendDot(Color color) => Container(
        width: 12.r,
        height: 12.r,
        decoration:
            BoxDecoration(shape: BoxShape.circle, color: color),
      );

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        await _onBackPressed();
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF7F9FB),
        body: _questions.isEmpty
            ? const SafeArea(
                child: Center(
                  child: CircularProgressIndicator(
                    color: Color(0xFF006B62),
                  ),
                ),
              )
            : SafeArea(
                child: Column(
                  children: [
                    _buildAppBar(),
                    LinearProgressIndicator(
                      value: (_currentIndex + 1) / _questions.length,
                      backgroundColor: const Color(0xFFE6E8EA),
                      valueColor: const AlwaysStoppedAnimation<Color>(
                          _primary),
                      minHeight: 6.h,
                    ),
                    Expanded(
                      child: SingleChildScrollView(
                        child: AnimatedSwitcher(
                          duration: const Duration(milliseconds: 300),
                          transitionBuilder: (child, animation) {
                            final offset = _isGoingForward
                                ? Tween(
                                    begin: const Offset(1, 0),
                                    end: Offset.zero,
                                  )
                                : Tween(
                                    begin: const Offset(-1, 0),
                                    end: Offset.zero,
                                  );
                            return SlideTransition(
                              position: offset.animate(animation),
                              child: child,
                            );
                          },
                          child: _buildQuestionCard(
                            key: ValueKey(_currentIndex),
                          ),
                        ),
                      ),
                    ),
                    _buildNavRow(),
                  ],
                ),
              ),
      ),
    );
  }
}
