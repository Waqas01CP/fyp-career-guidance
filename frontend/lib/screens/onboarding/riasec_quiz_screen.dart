import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/api_service.dart';

class RiasecQuizScreen extends ConsumerStatefulWidget {
  const RiasecQuizScreen({super.key});

  @override
  ConsumerState<RiasecQuizScreen> createState() => _RiasecQuizScreenState();
}

class _RiasecQuizScreenState extends ConsumerState<RiasecQuizScreen>
    with SingleTickerProviderStateMixin {
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

  late final AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _loadQuestions();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
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
        content:
            const Text('Your progress will be lost if you leave now.'),
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
      Navigator.pushNamedAndRemoveUntil(
          context, '/login', (route) => false);
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
        await ref.read(profileProvider.notifier).loadProfile(token);
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/riasec-complete');
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
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _selectedAnswer = score),
        borderRadius: BorderRadius.circular(12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          height: 52,
          decoration: BoxDecoration(
            color: isSelected ? _primary : _unselected,
            borderRadius: BorderRadius.circular(12),
          ),
          alignment: Alignment.center,
          padding: const EdgeInsets.symmetric(horizontal: 2),
          child: Text(
            label.toUpperCase(),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w600,
              color: isSelected ? Colors.white : _secondary,
              letterSpacing: 0.02,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInsightPanel(String insight) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Container(
        margin: const EdgeInsets.only(top: 20),
        decoration: const BoxDecoration(
          color: _tertiaryFixed,
          border: Border(
            left: BorderSide(color: _tertiary, width: 4),
          ),
        ),
        padding: const EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.auto_awesome, color: _tertiary, size: 18),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'AI INSIGHT',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.1,
                      color: _onTertiaryFixedVar,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    insight,
                    style: const TextStyle(
                      fontSize: 13,
                      color: _onTertiaryFixed,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionCard({required Key key}) {
    final q = _questions[_currentIndex];
    final dimension  = q['dimension'] as String;
    final questionText = q['text_en'] as String;
    final dimName    = _dimensionNames[dimension] ?? dimension;
    final insight    = _dimensionInsights[dimension];

    return Container(
      key: key,
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
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
                padding: const EdgeInsets.symmetric(
                    horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F4F6),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  dimName.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: _primary,
                    letterSpacing: 0.06,
                  ),
                ),
              ),
              Text(
                'Q${_currentIndex + 1} OF ${_questions.length}',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: _secondary,
                  letterSpacing: 0.08,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            questionText,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: _onSurface,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              for (int i = 1; i <= 5; i++) ...[
                _buildLikertButton(
                  i,
                  _scaleLabels['$i'] ?? '$i',
                  _selectedAnswer == i,
                ),
                if (i < 5) const SizedBox(width: 8),
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
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      color: const Color(0xFFF7F9FB),
      child: Row(
        children: [
          SizedBox(
            width: 48,
            height: 48,
            child: InkWell(
              onTap: _onBackPressed,
              borderRadius: BorderRadius.circular(8),
              child: const Icon(
                Icons.arrow_back,
                color: _secondary,
                size: 24,
              ),
            ),
          ),
          const SizedBox(width: 4),
          const Icon(Icons.school, color: _primary, size: 22),
          const SizedBox(width: 6),
          const Flexible(
            child: Text(
              'Academic Intelligence',
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: _primary,
              ),
            ),
          ),
          const Spacer(),
          const Text(
            'Step 1 of 3',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: _secondary,
            ),
          ),
          const SizedBox(width: 10),
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: _unselected,
            ),
            child: const Icon(Icons.person, size: 16, color: _secondary),
          ),
          const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildNavRow() {
    final isLast      = _currentIndex == _questions.length - 1;
    final isPrevDisabled = _currentIndex <= 0;
    final isSubmitEnabled = _selectedAnswer != null && !_isSubmitting;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
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
            icon: const Icon(Icons.arrow_back, size: 18),
            label: const Text('Previous'),
            style: TextButton.styleFrom(
              foregroundColor: _secondary,
              disabledForegroundColor: const Color(0xFFBDC9C6),
              padding: const EdgeInsets.symmetric(
                  horizontal: 16, vertical: 14),
              textStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          if (isLast)
            _buildViewResultsButton(isSubmitEnabled)
          else
            ElevatedButton.icon(
              onPressed: _selectedAnswer == null ? null : _onNext,
              icon: const Text('Next'),
              label: const Icon(Icons.arrow_forward, size: 18),
              style: ElevatedButton.styleFrom(
                backgroundColor: _primary,
                disabledBackgroundColor: const Color(0xFFE0E3E5),
                foregroundColor: Colors.white,
                disabledForegroundColor: const Color(0xFF6E7977),
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 0,
                textStyle: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildViewResultsButton(bool isEnabled) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isEnabled ? _onSubmit : null,
        borderRadius: BorderRadius.circular(14),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          height: 52,
          decoration: BoxDecoration(
            gradient: isEnabled
                ? const LinearGradient(
                    colors: [Color(0xFF6616D7), Color(0xFF7F3EF0)],
                  )
                : null,
            color: isEnabled ? null : const Color(0xFFE0E3E5),
            borderRadius: BorderRadius.circular(14),
          ),
          alignment: Alignment.center,
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: _isSubmitting
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(
                  'View My Results',
                  style: TextStyle(
                    fontSize: 15,
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
                      minHeight: 6,
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
