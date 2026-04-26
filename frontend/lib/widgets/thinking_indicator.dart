import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// ThinkingIndicator — three staggered bouncing dots in AI purple.
/// Shown in Chat screen when isStreaming == true and the last message has
/// empty content (i.e. no tokens received yet).
class ThinkingIndicator extends StatefulWidget {
  const ThinkingIndicator({super.key});

  @override
  State<ThinkingIndicator> createState() => _ThinkingIndicatorState();
}

class _ThinkingIndicatorState extends State<ThinkingIndicator>
    with TickerProviderStateMixin {
  static const Color _dotColor = Color(0xFF6616D7);
  static const int _dotCount = 3;

  late final List<AnimationController> _controllers;
  late final List<Animation<double>> _animations;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(_dotCount, (i) {
      final ctrl = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 600),
      );
      // Stagger: each dot starts 200ms after the previous
      Future.delayed(Duration(milliseconds: i * 200), () {
        if (mounted) ctrl.repeat(reverse: true);
      });
      return ctrl;
    });
    _animations = _controllers
        .map((ctrl) => Tween<double>(begin: 0, end: -8).animate(
              CurvedAnimation(parent: ctrl, curve: Curves.easeInOut),
            ))
        .toList();
  }

  @override
  void dispose() {
    for (final ctrl in _controllers) {
      ctrl.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4.h),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(_dotCount, (i) {
          return AnimatedBuilder(
            animation: _animations[i],
            builder: (context, _) => Transform.translate(
              offset: Offset(0, _animations[i].value),
              child: Container(
                margin: EdgeInsets.symmetric(horizontal: 3.w),
                width: 8.r,
                height: 8.r,
                decoration: const BoxDecoration(
                  color: _dotColor,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

