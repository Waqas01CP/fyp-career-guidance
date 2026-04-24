import 'package:flutter/material.dart';

class CarouselScreen extends StatefulWidget {
  const CarouselScreen({super.key});

  @override
  State<CarouselScreen> createState() => _CarouselScreenState();
}

class _CarouselScreenState extends State<CarouselScreen> {
  late final PageController _pageController;
  int _currentPage = 0;

  static const Color _bgColor = Color(0xFFF7F9FB);
  static const Color _primaryColor = Color(0xFF006B62);
  static const Color _secondaryColor = Color(0xFF515F74);
  static const Color _tertiaryColor = Color(0xFF6616D7);
  static const Color _tertiaryFixed = Color(0xFFEADDFF);
  static const Color _cardBg = Color(0xFFF2F4F6);
  static const Color _dotActive = Color(0xFF006B62);
  static const Color _dotInactive = Color(0xFFE0E3E5);
  static const Color _onSurface = Color(0xFF191C1E);

  // Slide 1 text from code_onboarding_carousel.html verbatim.
  // Slides 2–3: HTML mockup only shows slide 1; text sourced from design brief.
  static const List<Map<String, String>> _slides = [
    {
      'chip': 'INTEREST MAPPING',
      'headline': 'Discover What You ',
      'emphasis': 'Enjoy',
      'body':
          'Answer 60 questions about activities you enjoy. We use your responses to find degree programmes that genuinely fit you.',
    },
    {
      'chip': 'ACADEMIC INTELLIGENCE',
      'headline': 'Match your ',
      'emphasis': 'academic profile',
      'body':
          'Your grades and capability scores are matched against 200+ degree programmes across Karachi.',
    },
    {
      'chip': 'CAREER PATHWAYS',
      'headline': 'See your ',
      'emphasis': 'career future',
      'body':
          'Get ranked recommendations with market outlook, fees, and a personalised action roadmap.',
    },
  ];

  static const List<List<IconData>> _bentoIcons = [
    [Icons.psychology, Icons.auto_awesome],
    [Icons.school, Icons.auto_awesome],
    [Icons.trending_up, Icons.auto_awesome],
  ];

  static const List<List<String>> _bentoLabels = [
    ['REALISTIC', 'INVESTIGATIVE'],
    ['GRADES', 'CAPABILITY'],
    ['CAREERS', 'OUTLOOK'],
  ];

  static const List<String> _aptitudeLabels = [
    'APTITUDE MAP',
    'GRADE MATCH',
    'CAREER PATH',
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onNext() {
    if (_currentPage < _slides.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                physics: const BouncingScrollPhysics(),
                itemCount: _slides.length,
                onPageChanged: (index) => setState(() => _currentPage = index),
                itemBuilder: (context, index) =>
                    _buildSlide(_slides[index], index),
              ),
            ),
            _buildFooter(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: _primaryColor,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.school, color: Colors.white, size: 18),
              ),
              const SizedBox(width: 8),
              const Text(
                'Academic Intelligence',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: _primaryColor,
                ),
              ),
            ],
          ),
          TextButton(
            onPressed: () =>
                Navigator.pushReplacementNamed(context, '/login'),
            style: TextButton.styleFrom(
              foregroundColor: _secondaryColor,
              minimumSize: const Size(48, 48),
            ),
            child: const Text(
              'Skip',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSlide(Map<String, String> slide, int index) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        children: [
          AspectRatio(
            aspectRatio: 1.0,
            child: Container(
              decoration: BoxDecoration(
                color: _cardBg,
                borderRadius: BorderRadius.circular(40),
              ),
              padding: const EdgeInsets.all(20),
              child: _buildBentoGrid(index),
            ),
          ),
          const SizedBox(height: 32),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildChip(slide['chip']!),
              const SizedBox(height: 12),
              _buildHeadline(slide['headline']!, slide['emphasis']!),
              const SizedBox(height: 12),
              Text(
                slide['body']!,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w400,
                  color: _secondaryColor,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildChip(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: _tertiaryFixed,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.auto_awesome, size: 12, color: _tertiaryColor),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: _tertiaryColor,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeadline(String text, String emphasis) {
    return RichText(
      text: TextSpan(
        style: const TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.w700,
          color: _onSurface,
          letterSpacing: -0.6,
          height: 1.2,
          fontFamily: 'Inter',
        ),
        children: [
          TextSpan(text: text),
          TextSpan(
            text: emphasis,
            style: const TextStyle(
              fontStyle: FontStyle.italic,
              color: _primaryColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBentoGrid(int slideIndex) {
    return Row(
      children: [
        Expanded(
          child: Column(
            children: [
              Expanded(
                child: _BentoCell(
                  bg: Colors.white,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _bentoIcons[slideIndex][0],
                        color: _tertiaryColor,
                        size: 28,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _bentoLabels[slideIndex][0],
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: _secondaryColor,
                          letterSpacing: 1.2,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: _BentoCell(
                  bg: _tertiaryFixed,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: const BoxDecoration(
                          color: _tertiaryColor,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.auto_awesome,
                          size: 14,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _bentoLabels[slideIndex][1],
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: _tertiaryColor,
                          letterSpacing: 1.2,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _BentoCell(
            bg: const Color(0xFFECEEF0),
            child: _buildAptitudeVisual(_aptitudeLabels[slideIndex]),
          ),
        ),
      ],
    );
  }

  Widget _buildAptitudeVisual(String label) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: _primaryColor.withValues(alpha: 0.3),
              width: 1.5,
            ),
          ),
        ),
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: _tertiaryColor.withValues(alpha: 0.25),
              width: 1,
            ),
          ),
        ),
        Container(
          width: 18,
          height: 18,
          decoration: const BoxDecoration(
            color: _tertiaryFixed,
            shape: BoxShape.circle,
          ),
        ),
        Positioned(
          bottom: 14,
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 7,
              fontWeight: FontWeight.w700,
              color: Color(0xFF6E7977),
              letterSpacing: 1.0,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFooter() {
    final isLastSlide = _currentPage == _slides.length - 1;
    return Padding(
      padding: const EdgeInsets.fromLTRB(32, 32, 32, 48),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildDotIndicators(),
          _buildNextButton(isLastSlide),
        ],
      ),
    );
  }

  Widget _buildDotIndicators() {
    return Row(
      children: List.generate(_slides.length, (index) {
        final isActive = index == _currentPage;
        return Padding(
          padding: const EdgeInsets.only(right: 6),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: isActive ? 28.0 : 6.0,
            height: 3,
            decoration: BoxDecoration(
              color: isActive ? _dotActive : _dotInactive,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildNextButton(bool isLastSlide) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Color(0x40006B62),
            blurRadius: 20,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: ElevatedButton(
        onPressed: _onNext,
        style: ElevatedButton.styleFrom(
          backgroundColor: _primaryColor,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: Text(
          isLastSlide ? 'Get Started' : 'Next',
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _BentoCell extends StatelessWidget {
  const _BentoCell({required this.bg, required this.child});

  final Color bg;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF334155).withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: child,
    );
  }
}
