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

class AssessmentScreen extends ConsumerStatefulWidget {
  const AssessmentScreen({super.key});

  @override
  ConsumerState<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends ConsumerState<AssessmentScreen> {
  // ── Colour constants ──────────────────────────────────────────────────────
  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _surfaceLow = Color(0xFFF2F4F6);
  static const Color _surfaceHigh = Color(0xFFE6E8EA);
  static const Color _errorColor = Color(0xFFBA1A1A);

  // ── Subject metadata ──────────────────────────────────────────────────────
  static const List<String> _subjects = [
    'mathematics',
    'physics',
    'chemistry',
    'biology',
    'english',
  ];
  static const Map<String, String> _subjectLabels = {
    'mathematics': 'Math',
    'physics': 'Physics',
    'chemistry': 'Chemistry',
    'biology': 'Biology',
    'english': 'English',
  };

  // ── Storage ───────────────────────────────────────────────────────────────
  static const _storage = FlutterSecureStorage();

  // ── State ─────────────────────────────────────────────────────────────────
  List<Map<String, dynamic>> _questions = [];
  int _currentIndex = 0;
  final Map<String, int> _answers = {};
  bool _isSubmitting = false;
  bool _isGoingForward = true;

  Timer? _draftDebounce;
  late final ScrollController _tabScrollController;

  // ── Lifecycle ─────────────────────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    _tabScrollController = ScrollController();
    _loadAssessment();
  }

  @override
  void dispose() {
    _draftDebounce?.cancel();
    _tabScrollController.dispose();
    super.dispose();
  }

  // ── Computed getters ──────────────────────────────────────────────────────
  int get _activeSubjectIndex {
    if (_questions.isEmpty) return 0;
    final subject = _questions[_currentIndex]['subject'] as String? ?? 'mathematics';
    final idx = _subjects.indexOf(subject);
    return idx < 0 ? 0 : idx;
  }

  bool get _canSubmit =>
      _questions.isNotEmpty && _answers.length == _questions.length;

  // ── Question loading ──────────────────────────────────────────────────────
  String _getCurriculumLevel(String? eduLevel) {
    switch (eduLevel) {
      case 'matric':
      case 'o_level':
        return 'matric';
      case 'inter_part1':
        return 'inter_part1';
      default:
        return 'inter_part2';
    }
  }

  Future<void> _loadAssessment() async {
    final jsonStr =
        await rootBundle.loadString('assets/assessment_questions.json');
    final allQs = (jsonDecode(jsonStr) as List).cast<Map<String, dynamic>>();
    final level =
        _getCurriculumLevel(ref.read(profileProvider).educationLevel);

    const difficultyCount = {'easy': 3, 'medium': 5, 'hard': 4};
    final drawn = <Map<String, dynamic>>[];

    for (final subject in _subjects) {
      final subjectQs = <Map<String, dynamic>>[];
      for (final entry in difficultyCount.entries) {
        final pool = allQs
            .where((q) =>
                q['subject'] == subject &&
                q['curriculum_level'] == level &&
                q['difficulty'] == entry.key)
            .toList();
        pool.shuffle();
        subjectQs.addAll(pool.take(entry.value));
      }
      subjectQs.shuffle();
      drawn.addAll(subjectQs);
    }

    if (!mounted) return;
    setState(() => _questions = drawn);
    await _initDraft();
  }

  // ── Draft persistence ─────────────────────────────────────────────────────
  String _draftKey(String token) => 'assessment_draft_${token.hashCode}';

  Future<void> _initDraft() async {
    final token = ref.read(authProvider).token;
    if (token == null) return;

    final stage = ref.read(profileProvider).onboardingStage;
    if (stage != 'grades_complete') {
      try {
        await _storage.delete(key: _draftKey(token));
      } catch (_) {}
      return;
    }

    try {
      final raw = await _storage.read(key: _draftKey(token));
      if (raw == null || !mounted) return;
      final data = jsonDecode(raw) as Map<String, dynamic>;
      final savedIndex = ((data['currentIndex'] as int?) ?? 0)
          .clamp(0, (_questions.length - 1).clamp(0, 59));
      final savedAnswers =
          Map<String, dynamic>.from((data['answers'] as Map?) ?? {});
      setState(() {
        _currentIndex = savedIndex;
        for (final e in savedAnswers.entries) {
          _answers[e.key] = e.value as int;
        }
      });
    } catch (_) {
      // Corrupt draft — ignore silently
    }
  }

  Future<void> _saveDraft() async {
    final token = ref.read(authProvider).token;
    if (token == null) return;
    try {
      await _storage.write(
        key: _draftKey(token),
        value: jsonEncode({
          'currentIndex': _currentIndex,
          'answers': _answers,
        }),
      );
    } catch (_) {}
  }

  Future<void> _clearDraft() async {
    final token = ref.read(authProvider).token;
    if (token == null) return;
    try {
      await _storage.delete(key: _draftKey(token));
    } catch (_) {}
  }

  void _scheduleDraftSave() {
    _draftDebounce?.cancel();
    _draftDebounce =
        Timer(const Duration(milliseconds: 500), _saveDraft);
  }

  // ── Answer selection ──────────────────────────────────────────────────────
  void _onOptionSelected(int index) {
    final questionId = _questions[_currentIndex]['id'] as String;
    setState(() {
      _answers[questionId] = index;
    });
    _scheduleDraftSave();
  }

  // ── Navigation ────────────────────────────────────────────────────────────
  void _onPrevious() {
    if (_currentIndex <= 0) return;
    setState(() {
      _isGoingForward = false;
      _currentIndex--;
    });
    _scheduleDraftSave();
    _scrollTabIntoView();
  }

  void _onNext() {
    if (_currentIndex >= _questions.length - 1) return;
    setState(() {
      _isGoingForward = true;
      _currentIndex++;
    });
    _scheduleDraftSave();
    _scrollTabIntoView();
  }

  void _jumpToQuestion(int index) {
    if (index < 0 || index >= _questions.length) return;
    setState(() {
      _isGoingForward = index >= _currentIndex;
      _currentIndex = index;
    });
    _scheduleDraftSave();
    _scrollTabIntoView();
  }

  void _jumpToSubject(int subjectIndex) {
    final subjectName = _subjects[subjectIndex];
    final subjectEntries = _questions
        .asMap()
        .entries
        .where((e) => e.value['subject'] == subjectName)
        .toList();
    if (subjectEntries.isEmpty) return;

    // First unanswered, or first question if all answered
    final target = subjectEntries.firstWhere(
      (e) => !_answers.containsKey(e.value['id'] as String),
      orElse: () => subjectEntries.first,
    );
    _jumpToQuestion(target.key);
  }

  void _scrollTabIntoView() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_tabScrollController.hasClients) return;
      final approxTabWidth = 95.0.w;
      final target = (_activeSubjectIndex * approxTabWidth).clamp(
        0.0,
        _tabScrollController.position.maxScrollExtent,
      );
      _tabScrollController.animateTo(
        target,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeInOut,
      );
    });
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  Map<String, Map<String, int>> _computeSubjectResults() {
    final results = <String, Map<String, int>>{};
    for (final subject in _subjects) {
      final subjectQs =
          _questions.where((q) => q['subject'] == subject).toList();
      int correct = 0;
      for (final q in subjectQs) {
        final selected = _answers[q['id'] as String];
        if (selected != null && selected == (q['correct_index'] as int)) {
          correct++;
        }
      }
      results[subject] = {
        'correct': correct,
        'total': subjectQs.length,
      };
    }
    return results;
  }

  Future<void> _onSubmit() async {
    if (!_canSubmit || _isSubmitting) return;

    final token = ref.read(authProvider).token;
    if (token == null) return;

    setState(() => _isSubmitting = true);

    final Map<String, List<int>> responses = {};
    for (final subject in _subjects) {
      final subjectQs =
          _questions.where((q) => q['subject'] == subject).toList();
      responses[subject] = subjectQs.map((q) {
        final selected = _answers[q['id'] as String];
        return (selected == (q['correct_index'] as int)) ? 1 : 0;
      }).toList();
    }

    try {
      final response = await ApiService.post(
        '/profile/assessment',
        {'responses': responses},
        token: token,
      );

      if (response.statusCode == 200) {
        // Item 15: loadProfile BEFORE showing results overlay
        await ref.read(profileProvider.notifier).loadProfile(token);
        await _clearDraft();
        if (!mounted) return;
        setState(() => _isSubmitting = false);
        _showResultsBottomSheet();
      } else if (response.statusCode == 401) {
        if (!mounted) return;
        ref.read(authProvider.notifier).handleUnauthorized();
        Navigator.pushNamedAndRemoveUntil(
            context, '/login', (_) => false);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
            'Submission failed. Please try again.',
            style: TextStyle(fontSize: 14.sp),
          ),
          backgroundColor: _errorColor,
          duration: const Duration(seconds: 3),
        ));
        setState(() => _isSubmitting = false);
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
          'No connection. Check your internet and try again.',
          style: TextStyle(fontSize: 14.sp),
        ),
        backgroundColor: _errorColor,
        duration: const Duration(seconds: 3),
      ));
      setState(() => _isSubmitting = false);
    }
  }

  // ── Results bottom sheet ──────────────────────────────────────────────────
  void _showResultsBottomSheet() {
    final results = _computeSubjectResults();
    final totalCorrect =
        results.values.fold(0, (sum, v) => sum + v['correct']!);
    final overallPct = (totalCorrect / 60 * 100).round();

    showModalBottomSheet(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _ResultsSheet(
        results: results,
        totalCorrect: totalCorrect,
        overallPct: overallPct,
        subjectLabels: _subjectLabels,
        onViewFullReport: () {
          Navigator.pop(ctx);
          Navigator.pushReplacementNamed(context, '/assessment-complete');
        },
      ),
    );
  }

  // ── Question map bottom sheet ─────────────────────────────────────────────
  void _openQuestionMap() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _buildQuestionMapSheet(ctx),
    );
  }

  Future<void> _onBackPressed() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          'Leave assessment?',
          style: TextStyle(
              fontSize: 18.sp, fontWeight: FontWeight.w700),
        ),
        content: Text(
          'Your answers are saved and will be restored when you return.',
          style: TextStyle(fontSize: 14.sp),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('Stay', style: TextStyle(fontSize: 14.sp)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(
              'Leave',
              style: TextStyle(fontSize: 14.sp, color: _errorColor),
            ),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      Navigator.pop(context);
    }
  }

  // ── Build: Subject tabs ───────────────────────────────────────────────────
  Widget _buildSubjectTabs() {
    return Container(
      height: 52.h,
      color: Colors.white,
      child: ListView.builder(
        controller: _tabScrollController,
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
        itemCount: _subjects.length,
        itemBuilder: (ctx, i) {
          final subject = _subjects[i];
          final label = _subjectLabels[subject]!;
          final isActive = i == _activeSubjectIndex;
          final answered = _questions.isEmpty
              ? 0
              : _questions
                  .where((q) =>
                      q['subject'] == subject &&
                      _answers.containsKey(q['id'] as String))
                  .length;
          final total = _questions.isEmpty
              ? 12
              : _questions.where((q) => q['subject'] == subject).length;

          return GestureDetector(
            onTap: () => _jumpToSubject(i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: EdgeInsets.only(right: 8.w),
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              decoration: BoxDecoration(
                color: isActive ? _primary : _surfaceHigh,
                borderRadius: BorderRadius.circular(20.r),
              ),
              alignment: Alignment.center,
              child: Text(
                '$label $answered/$total',
                style: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w600,
                  color: isActive ? Colors.white : _secondary,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Build: Question card ──────────────────────────────────────────────────
  Widget _buildQuestionCard() {
    if (_questions.isEmpty) return const SizedBox.shrink();
    final q = _questions[_currentIndex];
    final subject = q['subject'] as String? ?? '';
    final questionText = q['question'] as String? ?? '';
    final options = (q['options'] as List).cast<String>();
    final questionId = q['id'] as String;
    final selectedOption = _answers[questionId];

    return Container(
      margin: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 0),
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
          // Subject badge
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: const Color(0xFFEADDFF),
              borderRadius: BorderRadius.circular(20.r),
            ),
            child: Text(
              subject.toUpperCase(),
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF5A00C6),
                letterSpacing: 0.9,
              ),
            ),
          ),
          SizedBox(height: 12.h),
          // Counter
          Text(
            'QUESTION ${_currentIndex + 1} OF ${_questions.length}',
            style: TextStyle(
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
              color: _secondary,
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(height: 12.h),
          // Question text
          Text(
            questionText,
            style: TextStyle(
              fontSize: 18.sp,
              fontWeight: FontWeight.w600,
              color: _onSurface,
              height: 1.5,
            ),
          ),
          SizedBox(height: 24.h),
          // Options
          ...options.asMap().entries.map((entry) =>
              _buildOption(entry.key, entry.value,
                  isSelected: selectedOption == entry.key)),
        ],
      ),
    );
  }

  // ── Build: Option button (no correct/wrong colours) ───────────────────────
  Widget _buildOption(int index, String text, {required bool isSelected}) {
    final letter = String.fromCharCode(65 + index);

    return GestureDetector(
      onTap: () => _onOptionSelected(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: EdgeInsets.only(bottom: 10.h),
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
        constraints: BoxConstraints(minHeight: 52.h),
        decoration: BoxDecoration(
          color: isSelected ? _primary : _surfaceLow,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Row(
          children: [
            Container(
              width: 32.w,
              height: 32.h,
              decoration: BoxDecoration(
                color: isSelected
                    ? Colors.white.withAlpha(64)
                    : _surfaceHigh,
                borderRadius: BorderRadius.circular(8.r),
              ),
              alignment: Alignment.center,
              child: Text(
                letter,
                style: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? Colors.white : _secondary,
                ),
              ),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w400,
                  color: isSelected ? Colors.white : _onSurface,
                ),
              ),
            ),
            if (isSelected) ...[
              SizedBox(width: 8.w),
              Icon(Icons.check_circle, color: Colors.white, size: 18.r),
            ],
          ],
        ),
      ),
    );
  }

  // ── Build: Bottom navigation bar ──────────────────────────────────────────
  Widget _buildBottomBar() {
    if (_questions.isEmpty) return const SizedBox.shrink();
    final remaining = _questions.length - _answers.length;
    final canGoPrev = _currentIndex > 0;
    final canGoNext = _currentIndex < _questions.length - 1;

    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
      decoration: const BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
              color: Color(0x0F191C1E),
              blurRadius: 8,
              offset: Offset(0, -2)),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              // Previous button
              TextButton(
                onPressed: canGoPrev ? _onPrevious : null,
                style: TextButton.styleFrom(
                  foregroundColor:
                      canGoPrev ? _primary : const Color(0xFFBDC9C6),
                  padding: EdgeInsets.symmetric(horizontal: 12.w),
                  minimumSize: Size(0, 44.h),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.arrow_back_rounded, size: 18.r),
                    SizedBox(width: 4.w),
                    Text('Prev', style: TextStyle(fontSize: 14.sp)),
                  ],
                ),
              ),
              const Spacer(),
              // Question map button
              IconButton(
                icon: Icon(Icons.grid_view_rounded,
                    size: 22.r, color: _secondary),
                onPressed: _openQuestionMap,
                tooltip: 'Question map',
              ),
              const Spacer(),
              // Next button
              TextButton(
                onPressed: canGoNext ? _onNext : null,
                style: TextButton.styleFrom(
                  foregroundColor:
                      canGoNext ? _primary : const Color(0xFFBDC9C6),
                  padding: EdgeInsets.symmetric(horizontal: 12.w),
                  minimumSize: Size(0, 44.h),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('Next', style: TextStyle(fontSize: 14.sp)),
                    SizedBox(width: 4.w),
                    Icon(Icons.arrow_forward_rounded, size: 18.r),
                  ],
                ),
              ),
            ],
          ),
          SizedBox(height: 8.h),
          // Submit / remaining count
          if (_canSubmit)
            SizedBox(
              width: double.infinity,
              height: 52.h,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _onSubmit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _primary,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: _primary.withAlpha(100),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                  elevation: 0,
                ),
                child: _isSubmitting
                    ? SizedBox(
                        width: 22.r,
                        height: 22.r,
                        child: const CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2),
                      )
                    : Text(
                        'Submit Assessment',
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
              ),
            )
          else
            Text(
              '$remaining question${remaining == 1 ? '' : 's'} remaining',
              style: TextStyle(
                fontSize: 14.sp,
                color: _primary,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
        ],
      ),
    );
  }

  // ── Build: Question map sheet ─────────────────────────────────────────────
  Widget _buildQuestionMapSheet(BuildContext ctx) {
    return DraggableScrollableSheet(
      initialChildSize: 0.65,
      maxChildSize: 0.92,
      minChildSize: 0.4,
      builder: (_, scrollController) => Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius:
              BorderRadius.vertical(top: Radius.circular(20.r)),
        ),
        child: Column(
          children: [
            SizedBox(height: 12.h),
            Container(
              width: 40.w,
              height: 4.h,
              decoration: BoxDecoration(
                color: _surfaceHigh,
                borderRadius: BorderRadius.circular(2.r),
              ),
            ),
            SizedBox(height: 16.h),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w),
              child: Row(
                children: [
                  Text(
                    'Question Map',
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w700,
                      color: _onSurface,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    '${_answers.length}/60 answered',
                    style: TextStyle(fontSize: 14.sp, color: _secondary),
                  ),
                ],
              ),
            ),
            SizedBox(height: 12.h),
            // Legend
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w),
              child: Row(
                children: [
                  _legendDot(const Color(0x1A006B62)),
                  SizedBox(width: 6.w),
                  Text('Answered',
                      style:
                          TextStyle(fontSize: 14.sp, color: _secondary)),
                  SizedBox(width: 16.w),
                  _legendDot(_surfaceLow, border: false),
                  SizedBox(width: 6.w),
                  Text('Unanswered',
                      style:
                          TextStyle(fontSize: 14.sp, color: _secondary)),
                  SizedBox(width: 16.w),
                  _legendDot(Colors.white, border: true),
                  SizedBox(width: 6.w),
                  Text('Current',
                      style:
                          TextStyle(fontSize: 14.sp, color: _secondary)),
                ],
              ),
            ),
            SizedBox(height: 16.h),
            Expanded(
              child: ListView(
                controller: scrollController,
                padding: EdgeInsets.symmetric(horizontal: 20.w),
                children: _subjects.map((subject) {
                  final label = _subjectLabels[subject]!;
                  final subjectEntries = _questions
                      .asMap()
                      .entries
                      .where((e) => e.value['subject'] == subject)
                      .toList();

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        label.toUpperCase(),
                        style: TextStyle(
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w700,
                          color: _secondary,
                          letterSpacing: 0.8,
                        ),
                      ),
                      SizedBox(height: 8.h),
                      Wrap(
                        spacing: 6.w,
                        runSpacing: 6.h,
                        children: subjectEntries.map((e) {
                          final qIndex = e.key;
                          final qId = e.value['id'] as String;
                          final isAnswered =
                              _answers.containsKey(qId);
                          final isCurrent = qIndex == _currentIndex;

                          Color bg;
                          Color? borderColor;
                          Color textColor;
                          if (isCurrent) {
                            bg = Colors.white;
                            borderColor = _primary;
                            textColor = _primary;
                          } else if (isAnswered) {
                            bg = const Color(0x1A006B62);
                            borderColor = null;
                            textColor = _primary;
                          } else {
                            bg = _surfaceLow;
                            borderColor = null;
                            textColor = _secondary;
                          }

                          return Semantics(
                            button: true,
                            label:
                                'Question ${qIndex + 1}, ${isCurrent ? 'current' : isAnswered ? 'answered' : 'unanswered'}',
                            child: GestureDetector(
                              onTap: () {
                                Navigator.pop(ctx);
                                _jumpToQuestion(qIndex);
                              },
                              child: Container(
                                width: 36.r,
                                height: 36.r,
                                decoration: BoxDecoration(
                                  color: bg,
                                  borderRadius:
                                      BorderRadius.circular(8.r),
                                  border: borderColor != null
                                      ? Border.all(
                                          color: borderColor, width: 2)
                                      : null,
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  '${qIndex + 1}',
                                  style: TextStyle(
                                    fontSize: 14.sp,
                                    fontWeight: FontWeight.w600,
                                    color: textColor,
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                      SizedBox(height: 20.h),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _legendDot(Color bg, {bool border = false}) {
    return Container(
      width: 14.r,
      height: 14.r,
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4.r),
        border:
            border ? Border.all(color: _primary, width: 1.5) : null,
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final answeredCount = _answers.length;
    final totalQuestions = _questions.isEmpty ? 60 : _questions.length;
    final progress =
        totalQuestions > 0 ? answeredCount / totalQuestions : 0.0;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        await _onBackPressed();
      },
      child: Scaffold(
        backgroundColor: _surfaceLow,
        appBar: PreferredSize(
          preferredSize: Size.fromHeight(52.h),
          child: AppBar(
            backgroundColor: Colors.white,
            elevation: 0,
            automaticallyImplyLeading: false,
            titleSpacing: 12,
            title: Row(
              children: [
                Icon(Icons.school, color: _primary, size: 20.r),
                const Spacer(),
                Text(
                  'Step 3 of 3',
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w500,
                    color: _secondary,
                  ),
                ),
                SizedBox(width: 4.w),
              ],
            ),
          ),
        ),
        body: SafeArea(
          child: Column(
            children: [
              // Sticky progress bar
              LinearProgressIndicator(
                value: progress,
                minHeight: 6.h,
                backgroundColor: _surfaceHigh,
                valueColor:
                    const AlwaysStoppedAnimation<Color>(_primary),
              ),
              // Subject tabs
              _buildSubjectTabs(),
              const Divider(height: 1, color: Color(0xFFE6E8EA)),
              // Main content
              Expanded(
                child: _questions.isEmpty
                    ? const Center(
                        child: CircularProgressIndicator(
                            color: _primary))
                    : _isSubmitting
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const CircularProgressIndicator(
                                    color: _primary),
                                SizedBox(height: 16.h),
                                Text(
                                  'Submitting assessment…',
                                  style: TextStyle(
                                    fontSize: 14.sp,
                                    color: _secondary,
                                  ),
                                ),
                              ],
                            ),
                          )
                        : GestureDetector(
                            onHorizontalDragEnd: (details) {
                              if (details.primaryVelocity == null) {
                                return;
                              }
                              if (details.primaryVelocity! < -300) {
                                _onNext();
                              } else if (details.primaryVelocity! >
                                  300) {
                                _onPrevious();
                              }
                            },
                            child: SingleChildScrollView(
                              child: AnimatedSwitcher(
                                duration:
                                    const Duration(milliseconds: 300),
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
                                child: Column(
                                  key: ValueKey(_currentIndex),
                                  children: [
                                    _buildQuestionCard(),
                                    SizedBox(height: 16.h),
                                  ],
                                ),
                              ),
                            ),
                          ),
              ),
              // Bottom navigation bar
              _buildBottomBar(),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Results sheet (separate widget so it stays on screen after parent rebuilds) ──
class _ResultsSheet extends StatelessWidget {
  final Map<String, Map<String, int>> results;
  final int totalCorrect;
  final int overallPct;
  final Map<String, String> subjectLabels;
  final VoidCallback onViewFullReport;

  static const List<String> _subjects = [
    'mathematics',
    'physics',
    'chemistry',
    'biology',
    'english',
  ];

  const _ResultsSheet({
    required this.results,
    required this.totalCorrect,
    required this.overallPct,
    required this.subjectLabels,
    required this.onViewFullReport,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Container(
        padding: EdgeInsets.fromLTRB(24.w, 20.h, 24.w, 32.h),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius:
              BorderRadius.vertical(top: Radius.circular(24.r)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Drag handle
            Container(
              width: 40.w,
              height: 4.h,
              decoration: BoxDecoration(
                color: const Color(0xFFE6E8EA),
                borderRadius: BorderRadius.circular(2.r),
              ),
            ),
            SizedBox(height: 24.h),
            // Icon
            Container(
              width: 64.r,
              height: 64.r,
              decoration: BoxDecoration(
                color: const Color(0xFFEADDFF),
                borderRadius: BorderRadius.circular(32.r),
              ),
              child: Icon(Icons.auto_awesome,
                  size: 32.r, color: const Color(0xFF6616D7)),
            ),
            SizedBox(height: 16.h),
            // Title
            Text(
              'Assessment Complete!',
              style: TextStyle(
                fontSize: 22.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF191C1E),
                letterSpacing: -0.3,
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              '$overallPct% overall · $totalCorrect/60 correct',
              style: TextStyle(
                  fontSize: 15.sp, color: const Color(0xFF515F74)),
            ),
            SizedBox(height: 24.h),
            // Subject breakdown
            ..._subjects.map((subject) {
              final label = subjectLabels[subject] ?? subject;
              final data = results[subject] ??
                  {'correct': 0, 'total': 12};
              final correct = data['correct']!;
              final total = data['total']!;
              final pct = total > 0 ? correct / total : 0.0;
              final barColor = pct >= 0.7
                  ? const Color(0xFF006B62)
                  : (pct >= 0.5
                      ? const Color(0xFFF59E0B)
                      : const Color(0xFFBA1A1A));

              return Padding(
                padding: EdgeInsets.only(bottom: 14.h),
                child: Row(
                  children: [
                    SizedBox(
                      width: 80.w,
                      child: Text(
                        label,
                        style: TextStyle(
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFF191C1E),
                        ),
                      ),
                    ),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4.r),
                        child: LinearProgressIndicator(
                          value: pct,
                          minHeight: 8.h,
                          backgroundColor: const Color(0xFFE6E8EA),
                          valueColor:
                              AlwaysStoppedAnimation<Color>(barColor),
                        ),
                      ),
                    ),
                    SizedBox(width: 12.w),
                    Text(
                      '$correct/$total',
                      style: TextStyle(
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w700,
                        color: barColor,
                      ),
                    ),
                  ],
                ),
              );
            }),
            SizedBox(height: 24.h),
            // CTA button
            SizedBox(
              width: double.infinity,
              height: 52.h,
              child: ElevatedButton(
                onPressed: onViewFullReport,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF006B62),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                  elevation: 0,
                ),
                child: Text(
                  'View Full Report',
                  style: TextStyle(
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w700,
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
