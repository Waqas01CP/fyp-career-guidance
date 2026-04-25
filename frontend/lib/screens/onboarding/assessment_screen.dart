import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/api_service.dart';

class AssessmentScreen extends ConsumerStatefulWidget {
  const AssessmentScreen({super.key});

  @override
  ConsumerState<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends ConsumerState<AssessmentScreen>
    with SingleTickerProviderStateMixin {
  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _error = Color(0xFFBA1A1A);

  List<Map<String, dynamic>> _questions = [];
  int _currentIndex = 0;
  final Map<String, int> _answers = {};
  int? _selectedOption;
  bool _showFeedback = false;
  bool _isSubmitting = false;
  bool _isGoingForward = true;
  Timer? _feedbackTimer;

  late final AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _loadAssessment();
  }

  @override
  void dispose() {
    _feedbackTimer?.cancel();
    _animController.dispose();
    super.dispose();
  }

  String _getCurriculumLevel(String? eduLevel) {
    switch (eduLevel) {
      case 'matric':
      case 'o_level':
        return 'matric';
      case 'inter_part1':
        return 'inter_part1';
      case 'inter_part2':
      case 'completed_inter':
      case 'a_level':
      default:
        return 'inter_part2';
    }
  }

  Future<void> _loadAssessment() async {
    final jsonStr =
        await rootBundle.loadString('assets/assessment_questions.json');
    final allQs =
        (jsonDecode(jsonStr) as List).cast<Map<String, dynamic>>();

    final level = _getCurriculumLevel(
        ref.read(profileProvider).educationLevel);

    const subjects = [
      'mathematics',
      'physics',
      'chemistry',
      'biology',
      'english',
    ];
    const difficultyCount = {
      'easy': 3,
      'medium': 5,
      'hard': 4,
    };
    final drawn = <Map<String, dynamic>>[];

    for (final subject in subjects) {
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

    if (mounted) setState(() => _questions = drawn);
  }

  void _onOptionSelected(int optionIndex) {
    if (_selectedOption != null) return;

    final questionId = _questions[_currentIndex]['id'] as String;

    setState(() {
      _selectedOption = optionIndex;
      _showFeedback = true;
      _answers[questionId] = optionIndex;
    });

    _feedbackTimer = Timer(const Duration(milliseconds: 800), () {
      if (!mounted) return;
      if (_currentIndex < _questions.length - 1) {
        setState(() {
          _isGoingForward = true;
          _currentIndex++;
          _selectedOption = null;
          _showFeedback = false;
        });
      } else {
        _onSubmit();
      }
    });
  }

  // ignore: unused_element
  double _computeSubjectScore(String subject, Map<String, int> answers) {
    final subjectQs =
        _questions.where((q) => q['subject'] == subject).toList();
    if (subjectQs.isEmpty) return 50.0;
    int correct = 0;
    for (final q in subjectQs) {
      final selected = answers[q['id'] as String];
      if (selected == q['correct_index'] as int) correct++;
    }
    return (correct / subjectQs.length * 100).roundToDouble();
  }

  Future<void> _onSubmit() async {
    final token = ref.read(authProvider).token;
    if (token == null) return;

    if (!mounted) return;
    setState(() => _isSubmitting = true);

    const subjects = [
      'mathematics',
      'physics',
      'chemistry',
      'biology',
      'english',
    ];
    final Map<String, List<int>> responses = {};

    for (final subject in subjects) {
      final subjectQs =
          _questions.where((q) => q['subject'] == subject).toList();
      final flags = subjectQs.map((q) {
        final correctIndex = q['correct_index'] as int;
        final selected = _answers[q['id'] as String];
        return (selected == correctIndex) ? 1 : 0;
      }).toList();
      responses[subject] = flags;
    }

    try {
      final response = await ApiService.post(
        '/profile/assessment',
        {'responses': responses},
        token: token,
      );

      if (response.statusCode == 200) {
        await ref.read(profileProvider.notifier).loadProfile(token);
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/assessment-complete');
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Submission failed. Try again.'),
            backgroundColor: Color(0xFFBA1A1A),
          ),
        );
        setState(() => _isSubmitting = false);
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No connection. Check your internet.'),
          backgroundColor: Color(0xFFBA1A1A),
        ),
      );
      setState(() => _isSubmitting = false);
    }
  }

  Future<void> _onBackPressed() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Leave assessment?'),
        content: const Text(
          'Your progress will be lost. The assessment will restart from the beginning next time.',
        ),
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
      Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
    }
  }

  Widget _buildOption(
    int index,
    String text,
    bool isSelected,
    bool showFeedback,
    int correctIndex,
  ) {
    // 0x0D = ~5% opacity, 0x26 = ~15% opacity
    Color bg = const Color(0xFFF2F4F6);
    Color textColor = _onSurface;
    Color badgeBg = const Color(0xFFE6E8EA);
    Color badgeColor = _secondary;
    Widget? trailing;

    if (showFeedback) {
      if (index == correctIndex) {
        bg = const Color(0x0D006B62);
        textColor = _primary;
        badgeBg = const Color(0x26006B62);
        badgeColor = _primary;
        trailing = const Icon(Icons.check_circle,
            color: Color(0xFF006B62), size: 18);
      } else if (isSelected) {
        bg = const Color(0xFFFFEDEA);
        textColor = _error;
        badgeBg = const Color(0x26BA1A1A);
        badgeColor = _error;
        trailing = const Icon(Icons.cancel,
            color: Color(0xFFBA1A1A), size: 18);
      }
    } else if (isSelected) {
      bg = const Color(0x0D006B62);
      badgeBg = _primary;
      badgeColor = Colors.white;
      trailing = const Icon(Icons.check_circle,
          color: Color(0xFF006B62), size: 18);
    }

    final letter = String.fromCharCode(65 + index);

    return GestureDetector(
      onTap: (_showFeedback || _selectedOption != null)
          ? null
          : () => _onOptionSelected(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(12),
          border: (isSelected && !showFeedback)
              ? const Border(
                  left: BorderSide(color: Color(0xFF006B62), width: 3))
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: badgeBg,
                borderRadius: BorderRadius.circular(8),
              ),
              alignment: Alignment.center,
              child: Text(
                letter,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: badgeColor,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  color: textColor,
                ),
              ),
            ),
            if (trailing != null) ...[
              const SizedBox(width: 8),
              trailing,
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionCard({required Key key}) {
    final q = _questions[_currentIndex];
    final subject = q['subject'] as String? ?? '';
    final questionText = q['question'] as String? ?? '';
    final options = (q['options'] as List).cast<String>();
    final correctIndex = q['correct_index'] as int;

    return Container(
      key: key,
      margin: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
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
            padding:
                const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFEADDFF),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              subject.toUpperCase(),
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                color: Color(0xFF5A00C6),
                letterSpacing: 0.9,
              ),
            ),
          ),
          const SizedBox(height: 12),
          // Counter
          Text(
            'QUESTION ${_currentIndex + 1} OF ${_questions.length}',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: Color(0xFF515F74),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          // Question text
          Text(
            questionText,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w600,
              color: Color(0xFF191C1E),
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),
          // Options A–D
          ...options.asMap().entries.map((entry) => _buildOption(
                entry.key,
                entry.value,
                _selectedOption == entry.key,
                _showFeedback,
                correctIndex,
              )),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final answeredCount = _answers.length;
    final totalQuestions = _questions.isEmpty ? 60 : _questions.length;
    final progress =
        totalQuestions > 0 ? answeredCount / totalQuestions : 0.0;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        await _onBackPressed();
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF2F4F6),
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(52),
          child: AppBar(
            backgroundColor: Colors.white,
            elevation: 0,
            automaticallyImplyLeading: false,
            titleSpacing: 12,
            title: Row(
              children: [
                const Icon(Icons.school, color: _primary, size: 20),
                const SizedBox(width: 8),
                const Text(
                  'Academic Intelligence',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: _primary,
                  ),
                ),
                const Spacer(),
                const Text(
                  'Step 3 of 3',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: _secondary,
                  ),
                ),
                const SizedBox(width: 4),
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
                minHeight: 6,
                backgroundColor: const Color(0xFFE6E8EA),
                valueColor:
                    const AlwaysStoppedAnimation<Color>(_primary),
              ),
              // Body
              Expanded(
                child: _questions.isEmpty
                    ? const Center(
                        child: CircularProgressIndicator(color: _primary),
                      )
                    : _isSubmitting
                        ? const Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                CircularProgressIndicator(color: _primary),
                                SizedBox(height: 16),
                                Text(
                                  'Submitting assessment…',
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: _secondary,
                                  ),
                                ),
                              ],
                            ),
                          )
                        : SingleChildScrollView(
                            child: Column(
                              children: [
                                AnimatedSwitcher(
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
                                  child: _buildQuestionCard(
                                    key: ValueKey(_currentIndex),
                                  ),
                                ),
                                const SizedBox(height: 32),
                              ],
                            ),
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
