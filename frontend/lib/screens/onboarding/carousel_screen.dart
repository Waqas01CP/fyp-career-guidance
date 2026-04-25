import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

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
      padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 32.w,
                height: 32.h,
                decoration: BoxDecoration(
                  color: _primaryColor,
                  borderRadius: BorderRadius.circular(8.r),
                ),
                child: Icon(Icons.school, color: Colors.white, size: 18.r),
              ),
              SizedBox(width: 8.w),
              Text(
                'Academic Intelligence',
                style: TextStyle(
                  fontSize: 14.sp,
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
            child: Text(
              'Skip',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSlide(Map<String, String> slide, int index) {
    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32.w),
        child: Column(
          children: [
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 280, maxWidth: 280),
              child: AspectRatio(
                aspectRatio: 1.0,
                child: Container(
                  decoration: BoxDecoration(
                    color: _cardBg,
                    borderRadius: BorderRadius.circular(40.r),
                  ),
                  padding: EdgeInsets.all(20.r),
                  child: _buildBentoGrid(index),
                ),
              ),
            ),
          SizedBox(height: 32.h),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildChip(slide['chip']!),
              SizedBox(height: 12.h),
              _buildHeadline(slide['headline']!, slide['emphasis']!),
              SizedBox(height: 12.h),
              Text(
                slide['body']!,
                style: TextStyle(
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w400,
                  color: _secondaryColor,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ],
      ),
    ),
    );
  }

  Widget _buildChip(String label) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: _tertiaryFixed,
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 12.r, color: _tertiaryColor),
          SizedBox(width: 4.w),
          Text(
            label,
            style: TextStyle(
              fontSize: 10.sp,
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
        style: TextStyle(
          fontSize: 30.sp,
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
                        size: 28.r,
                      ),
                      SizedBox(height: 4.h),
                      Text(
                        _bentoLabels[slideIndex][0],
                        style: TextStyle(
                          fontSize: 9.sp,
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
              SizedBox(height: 8.h),
              Expanded(
                child: _BentoCell(
                  bg: _tertiaryFixed,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: EdgeInsets.all(6.r),
                        decoration: const BoxDecoration(
                          color: _tertiaryColor,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.auto_awesome,
                          size: 14.r,
                          color: Colors.white,
                        ),
                      ),
                      SizedBox(height: 4.h),
                      Text(
                        _bentoLabels[slideIndex][1],
                        style: TextStyle(
                          fontSize: 9.sp,
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
        SizedBox(width: 8.w),
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
          width: 72.w,
          height: 72.h,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: _primaryColor.withValues(alpha: 0.3),
              width: 1.5,
            ),
          ),
        ),
        Container(
          width: 46.w,
          height: 46.h,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: _tertiaryColor.withValues(alpha: 0.25),
              width: 1,
            ),
          ),
        ),
        Container(
          width: 18.w,
          height: 18.h,
          decoration: const BoxDecoration(
            color: _tertiaryFixed,
            shape: BoxShape.circle,
          ),
        ),
        Positioned(
          bottom: 14,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 10.sp,
              fontWeight: FontWeight.w700,
              color: Color(0xFF515F74),
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
      padding: EdgeInsets.fromLTRB(32.w, 32.h, 32.w, 48.h),
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
          padding: EdgeInsets.only(right: 6.w),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: isActive ? 28.0 : 6.0,
            height: 3.h,
            decoration: BoxDecoration(
              color: isActive ? _dotActive : _dotInactive,
              borderRadius: BorderRadius.circular(2.r),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildNextButton(bool isLastSlide) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12.r),
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
          padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 16.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.r),
          ),
          elevation: 0,
        ),
        child: Text(
          isLastSlide ? 'Get Started' : 'Next',
          style: TextStyle(
            fontSize: 15.sp,
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
        borderRadius: BorderRadius.circular(16.r),
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
