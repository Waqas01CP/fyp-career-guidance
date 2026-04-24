import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/profile_provider.dart';

class RiasecCompleteScreen extends ConsumerWidget {
  const RiasecCompleteScreen({super.key});

  static const Map<String, int> _demoScores = {
    'R': 32, 'I': 45, 'A': 28, 'S': 31, 'E': 38, 'C': 42,
  };

  static const Map<String, String> _dimensionNames = {
    'R': 'Realistic',
    'I': 'Investigative',
    'A': 'Artistic',
    'S': 'Social',
    'E': 'Enterprising',
    'C': 'Conventional',
  };

  static int _scoreToPercent(int score) =>
      ((score - 10) / 40 * 100).round().clamp(0, 100);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final raw = ref.watch(profileProvider).riasecScores;
    final scores = raw.isEmpty
        ? _demoScores
        : raw.map((k, v) => MapEntry(k, (v as num).toInt()));

    final sorted = scores.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final topThree = sorted.take(3).toList();

    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FB),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 32, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildHeroBlock(),
              const SizedBox(height: 32),
              _buildResultsCard(scores),
              const SizedBox(height: 20),
              _buildTopThreePills(topThree),
              const SizedBox(height: 24),
              _buildInsightPanel(),
              const SizedBox(height: 32),
              _buildContinueButton(context),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeroBlock() {
    return Column(
      children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF006B62), Color(0xFF00857A)],
            ),
            boxShadow: const [
              BoxShadow(
                color: Color(0x4C006B62),
                blurRadius: 32,
                offset: Offset(0, 12),
              ),
            ],
          ),
          child: const Icon(
            Icons.psychology,
            size: 40,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 20),
        const Text(
          'RIASEC PROFILE COMPLETE',
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.1,
            color: Color(0xFF515F74),
          ),
        ),
        const SizedBox(height: 12),
        const Text(
          'Your Interest Profile',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.02 * 28,
            color: Color(0xFF191C1E),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Here\'s how your interests map across the six RIASEC dimensions.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w400,
            color: Color(0xFF515F74),
            height: 1.6,
          ),
        ),
      ],
    );
  }

  Widget _buildResultsCard(Map<String, int> scores) {
    return Container(
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
        children: [
          const Text(
            'INTEREST RADAR',
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.1,
              color: Color(0xFF515F74),
            ),
          ),
          const SizedBox(height: 16),
          Semantics(
            label: 'RIASEC radar chart showing your interest profile',
            child: AspectRatio(
              aspectRatio: 1.0,
              child: CustomPaint(
                painter: _RiasecRadarPainter(scores),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopThreePills(List<MapEntry<String, int>> topThree) {
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: 8,
      runSpacing: 8,
      children: topThree.map((entry) {
        final name = _dimensionNames[entry.key] ?? entry.key;
        final pct  = _scoreToPercent(entry.value);
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF006B62).withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            '$name · $pct%',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF006B62),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildInsightPanel() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: const BoxDecoration(
          color: Color(0xFFEADDFF),
          border: Border(
            left: BorderSide(color: Color(0xFF6616D7), width: 4),
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Icon(Icons.auto_awesome, color: Color(0xFF6616D7), size: 18),
            SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'AI INSIGHT',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.1,
                      color: Color(0xFF5A00C6),
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'Your RIASEC profile captures how you naturally engage with the world. The top dimensions shown above will guide our university and degree recommendations — programs where students with similar profiles tend to thrive.',
                    style: TextStyle(
                      fontSize: 13,
                      color: Color(0xFF25005A),
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

  Widget _buildContinueButton(BuildContext context) {
    return ElevatedButton(
      onPressed: () =>
          Navigator.pushReplacementNamed(context, '/grades-input'),
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF006B62),
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        padding: const EdgeInsets.all(18),
        elevation: 0,
      ),
      child: const Text(
        'Continue to Academic Grades',
        style: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
    );
  }
}

class _RiasecRadarPainter extends CustomPainter {
  final Map<String, int> scores;

  const _RiasecRadarPainter(this.scores);

  static const List<String> _dims = ['R', 'I', 'A', 'S', 'E', 'C'];
  static const double _minScore = 10.0;
  static const double _maxScore = 50.0;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.38;

    final gridPaint = Paint()
      ..color = const Color(0xFF6E7977).withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // Draw 3 concentric hexagonal tiers at 33%, 66%, 100%
    for (final tier in [0.33, 0.66, 1.0]) {
      final path = Path();
      for (int i = 0; i < 6; i++) {
        final angle = (i * 60 - 90) * pi / 180;
        final pt = Offset(
          center.dx + radius * tier * cos(angle),
          center.dy + radius * tier * sin(angle),
        );
        if (i == 0) {
          path.moveTo(pt.dx, pt.dy);
        } else {
          path.lineTo(pt.dx, pt.dy);
        }
      }
      path.close();
      canvas.drawPath(path, gridPaint);
    }

    // Draw axis lines from centre to each vertex
    for (int i = 0; i < 6; i++) {
      final angle = (i * 60 - 90) * pi / 180;
      canvas.drawLine(
        center,
        Offset(
          center.dx + radius * cos(angle),
          center.dy + radius * sin(angle),
        ),
        gridPaint,
      );
    }

    // Draw data polygon
    final dataPath = Path();
    final fillPaint = Paint()
      ..color = const Color(0xFF006B62).withValues(alpha: 0.15)
      ..style = PaintingStyle.fill;
    final strokePaint = Paint()
      ..color = const Color(0xFF006B62)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    for (int i = 0; i < 6; i++) {
      final dim   = _dims[i];
      final score = (scores[dim] ?? 10).toDouble();
      final normalized =
          ((score - _minScore) / (_maxScore - _minScore)).clamp(0.0, 1.0);
      final angle = (i * 60 - 90) * pi / 180;
      final pt = Offset(
        center.dx + radius * normalized * cos(angle),
        center.dy + radius * normalized * sin(angle),
      );
      if (i == 0) {
        dataPath.moveTo(pt.dx, pt.dy);
      } else {
        dataPath.lineTo(pt.dx, pt.dy);
      }
    }
    dataPath.close();
    canvas.drawPath(dataPath, fillPaint);
    canvas.drawPath(dataPath, strokePaint);

    // Draw vertex labels
    const labelStyle = TextStyle(
      fontSize: 10,
      fontWeight: FontWeight.w600,
      color: Color(0xFF515F74),
    );
    for (int i = 0; i < 6; i++) {
      final angle       = (i * 60 - 90) * pi / 180;
      final labelRadius = radius * 1.2;
      final labelOffset = Offset(
        center.dx + labelRadius * cos(angle),
        center.dy + labelRadius * sin(angle),
      );
      final painter = TextPainter(
        text: TextSpan(text: _dims[i], style: labelStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      painter.paint(
        canvas,
        labelOffset -
            Offset(painter.width / 2, painter.height / 2),
      );
    }
  }

  @override
  bool shouldRepaint(_RiasecRadarPainter old) => old.scores != scores;
}
