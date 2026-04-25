import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/profile_provider.dart';

class AssessmentCompleteScreen extends ConsumerWidget {
  const AssessmentCompleteScreen({super.key});

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

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final raw = ref.watch(profileProvider).capabilityScores;
    final scores = raw.isEmpty
        ? _demoScores
        : raw.map((k, v) => MapEntry(k, (v as num).toDouble()));

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F6),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 40, 20, 40),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Profile Complete badge
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F4F6),
                  borderRadius: BorderRadius.circular(20),
                  border:
                      Border.all(color: const Color(0xFFBDC9C6)),
                ),
                child: const Text(
                  'PROFILE COMPLETE',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF515F74),
                    letterSpacing: 0.9,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              // Hero icon — auto_awesome in purple circle
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  color: const Color(0xFFEADDFF),
                  borderRadius: BorderRadius.circular(48),
                ),
                child: const Icon(
                  Icons.auto_awesome,
                  size: 40,
                  color: Color(0xFF6616D7),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                "You're Ready",
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF191C1E),
                  letterSpacing: -0.56,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Your capability profile is complete. Here\'s how you performed across the five subjects.',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w400,
                  color: Color(0xFF515F74),
                  height: 1.6,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              // Subject scores card
              Container(
                width: double.infinity,
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
                    const Text(
                      'SUBJECT SCORES',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF515F74),
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ..._subjectOrder.map(
                      (s) => _buildSubjectRow(s, scores[s] ?? 50.0),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              // AI insight panel
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFEADDFF),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.auto_awesome,
                        size: 16, color: Color(0xFF6616D7)),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Your AI career guidance is now ready. These results, combined with your interests and academic grades, will power your personalised degree recommendations.',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w400,
                          color: Color(0xFF25005A),
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              // Continue button
              ElevatedButton(
                onPressed: () =>
                    Navigator.pushReplacementNamed(context, '/chat'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF006B62),
                  minimumSize: const Size(double.infinity, 56),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  padding: const EdgeInsets.all(18),
                  shadowColor: const Color(0x40006B62),
                  elevation: 8,
                ),
                child: const Text(
                  'Start My Career Guidance',
                  style: TextStyle(
                    fontSize: 15,
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

  static Widget _buildSubjectRow(String subject, double score) {
    final isStrong = score >= 70;
    final color =
        isStrong ? const Color(0xFF006B62) : const Color(0xFF515F74);
    final name = _subjectNames[subject] ?? subject;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              name,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: Color(0xFF191C1E),
              ),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: LinearProgressIndicator(
                value: score / 100,
                minHeight: 6,
                backgroundColor: const Color(0xFFE6E8EA),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 40,
            child: Text(
              '${score.toStringAsFixed(0)}%',
              style: TextStyle(
                fontSize: 13,
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
