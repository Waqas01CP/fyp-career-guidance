import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();

  bool _obscurePassword = true;
  bool _rememberMe = false;
  bool _isLoading = false;
  bool _signInPressed = false;
  bool _signUpPressed = false;

  // Design system tokens
  static const Color _bgColor       = Color(0xFFF7F9FB);
  static const Color _primaryColor   = Color(0xFF006B62);
  static const Color _gradientEnd    = Color(0xFF00857A);
  static const Color _fieldFill      = Color(0xFFF2F4F6);
  static const Color _secondaryColor = Color(0xFF515F74);
  static const Color _onSurface      = Color(0xFF191C1E);
  static const Color _errorColor     = Color(0xFFBA1A1A);

  @override
  void initState() {
    super.initState();
    _emailFocus.addListener(() => setState(() {}));
    _passwordFocus.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  String _routeForStage(String stage) {
    switch (stage) {
      case 'not_started':
        return '/riasec-quiz';
      case 'riasec_complete':
        return '/grades-input';
      case 'grades_complete':
        return '/assessment';
      case 'assessment_complete':
      case 'complete':
        // Preferences (Step 4) are optional — once assessment is done,
        // the user is fully onboarded. Send directly to chat.
        return '/chat';
      default:
        return '/riasec-quiz';
    }
  }

  Future<void> _onSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    final success = await ref.read(authProvider.notifier).login(
          _emailController.text.trim(),
          _passwordController.text,
        );
    if (!mounted) return;
    if (!success) {
      setState(() => _isLoading = false);
      // Error is shown via ref.listen below — do not set inline state here
      return;
    }
    final authState = ref.read(authProvider);
    await ref.read(profileProvider.notifier).loadProfile(authState.token!);
    if (!mounted) return;
    final profile = ref.read(profileProvider);
    Navigator.pushReplacementNamed(
        context, _routeForStage(profile.onboardingStage));
  }

  @override
  Widget build(BuildContext context) {
    // Show SnackBar on auth error — never inline text that shifts layout
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.error != null &&
          next.error != previous?.error &&
          mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.error!),
            backgroundColor: const Color(0xFF2D3133),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12.r),
            ),
          ),
        );
      }
    });

    return Scaffold(
      backgroundColor: _bgColor,
      resizeToAvoidBottomInset: false,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            // Use full screen height to determine compact mode, ignoring keyboard
            final isCompact = (constraints.maxHeight - MediaQuery.of(context).viewInsets.bottom) < 600;
            final vGap = isCompact ? 10.h : 20.h;
            final cardPadding = isCompact ? 18.r : 28.r;
            final topPadding = isCompact ? 8.h : 24.h;

            return CustomScrollView(
              physics: const ClampingScrollPhysics(),
              slivers: [
                SliverFillRemaining(
                  hasScrollBody: false,
                  child: Padding(
                    padding: EdgeInsets.only(
                      left: 24.w,
                      right: 24.w,
                      top: topPadding,
                      bottom: 24.h + MediaQuery.of(context).viewInsets.bottom,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _buildGradientBar(),
                        _buildFormCard(cardPadding),
                        SizedBox(height: vGap),
                        _buildSignUpRow(),
                      ],
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildGradientBar() {
    return Container(
      height: 3.h,
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [_primaryColor, _gradientEnd],
        ),
      ),
    );
  }

  Widget _buildFormCard(double cardPadding) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(32.r),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0F334155),
            blurRadius: 40,
            offset: Offset(0, 12),
          ),
        ],
      ),
      padding: EdgeInsets.all(cardPadding),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Semantics(
              header: true,
              child: Text(
                'Welcome Back',
                style: TextStyle(
                  fontSize: 28.sp,
                  fontWeight: FontWeight.w700,
                  color: _onSurface,
                  letterSpacing: -0.56,
                ),
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              'Enter your email and password to continue.',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w400,
                color: _secondaryColor,
                height: 1.6,
              ),
            ),
            SizedBox(height: 24.h),
            AutofillGroup(
              child: Column(
                children: [
                  _buildField(
                    controller: _emailController,
                    focusNode: _emailFocus,
                    label: 'Email Address',
                    semanticsLabel: 'Email address input',
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    autofillHints: const [AutofillHints.email],
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      if (!v.contains('@')) return 'Invalid email';
                      return null;
                    },
                  ),
                  SizedBox(height: 16.h),
                  _buildField(
                    controller: _passwordController,
                    focusNode: _passwordFocus,
                    label: 'Password',
                    semanticsLabel: 'Password input',
                    textInputAction: TextInputAction.done,
                    autofillHints: const [AutofillHints.password],
                    obscureText: _obscurePassword,
                    onFieldSubmitted: (_) => _onSubmit(),
                    suffixIcon: Semantics(
                      label: _obscurePassword
                          ? 'Show password'
                          : 'Hide password',
                      button: true,
                      child: IconButton(
                        onPressed: () => setState(
                            () => _obscurePassword = !_obscurePassword),
                        icon: Icon(
                          _obscurePassword
                              ? Icons.visibility_off
                              : Icons.visibility,
                          color: _secondaryColor,
                          size: 20.r,
                        ),
                      ),
                    ),
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      return null;
                    },
                  ),
                ],
              ),
            ),
            SizedBox(height: 8.h),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Semantics(
                    label: 'Remember this device checkbox',
                    child: Row(
                      children: [
                        SizedBox(
                          width: 24.w,
                          height: 24.h,
                          child: Checkbox(
                            value: _rememberMe,
                            onChanged: (v) =>
                                setState(() => _rememberMe = v ?? false),
                            activeColor: _primaryColor,
                            materialTapTargetSize:
                                MaterialTapTargetSize.padded,
                          ),
                        ),
                        SizedBox(width: 8.w),
                        Expanded(
                          child: Text(
                            'Remember this device',
                            style: TextStyle(
                              fontSize: 13.sp,
                              fontWeight: FontWeight.w400,
                              color: _secondaryColor,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                // Forgot Password — permanently disabled (no backend endpoint).
                // Per CLAUDE.md: "Forgot Password (demo) = Static coming soon.
                // No backend endpoint for demo."
                Semantics(
                  label: 'Forgot password — coming soon',
                  button: true,
                  child: TextButton(
                    onPressed: null, // Never enable — no backend endpoint
                    child: Text(
                      'Forgot Password?',
                      style: TextStyle(
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w600,
                        // Slate color (disabled) — not primary teal
                        color: _secondaryColor,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 24.h),
            // Sign In button with 0.97 scale press animation (Task 5a)
            Semantics(
              label: 'Sign in',
              button: true,
              child: GestureDetector(
                onTapDown: (_) => setState(() => _signInPressed = true),
                onTapUp: (_) => setState(() => _signInPressed = false),
                onTapCancel: () => setState(() => _signInPressed = false),
                child: AnimatedScale(
                  scale: _signInPressed ? 0.97 : 1.0,
                  duration: const Duration(milliseconds: 150),
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _onSubmit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _primaryColor,
                      disabledBackgroundColor:
                          _primaryColor.withValues(alpha: 0.7),
                      minimumSize: Size(double.infinity, 52.h),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14.r),
                      ),
                      elevation: 0,
                    ),
                    child: _isLoading
                        ? SizedBox(
                            height: 20.r,
                            width: 20.r,
                            child: const CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            'Sign In',
                            style: TextStyle(
                              fontSize: 15.sp,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                  ),
                ),
              ),
            ),
            // No inline error text — errors are shown via SnackBar in ref.listen above.
            // This prevents form card height shifting when errors appear/disappear.
          ],
        ),
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required FocusNode focusNode,
    required String label,
    required String semanticsLabel,
    TextInputType keyboardType = TextInputType.text,
    TextInputAction textInputAction = TextInputAction.next,
    List<String>? autofillHints,
    bool obscureText = false,
    Widget? suffixIcon,
    ValueChanged<String>? onFieldSubmitted,
    String? Function(String?)? validator,
  }) {
    return Semantics(
      label: semanticsLabel,
      textField: true,
      child: Stack(
        children: [
          TextFormField(
            controller: controller,
            focusNode: focusNode,
            keyboardType: keyboardType,
            textInputAction: textInputAction,
            autofillHints: autofillHints,
            obscureText: obscureText,
            onFieldSubmitted: onFieldSubmitted,
            style: TextStyle(
              fontSize: 15.sp,
              fontWeight: FontWeight.w400,
              color: _onSurface,
            ),
            decoration: InputDecoration(
              filled: true,
              fillColor: _fieldFill,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12.r),
                borderSide: BorderSide.none,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12.r),
                borderSide: BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12.r),
                borderSide: BorderSide.none,
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12.r),
                borderSide: BorderSide.none,
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12.r),
                borderSide: BorderSide.none,
              ),
              labelText: label,
              labelStyle: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w600,
                color: _secondaryColor,
                letterSpacing: 0.48,
              ),
              errorStyle: TextStyle(fontSize: 11.sp, color: _errorColor),
              suffixIcon: suffixIcon,
              contentPadding:
                  EdgeInsets.symmetric(horizontal: 16.w, vertical: 18.h),
            ),
            validator: validator,
          ),
          // Left-border focus indicator (DESIGN_HANDOFF spec)
          // Flutter InputDecoration has no native left-border-only focus.
          // Solution: Positioned overlay that appears on FocusNode.hasFocus.
          Positioned(
            left: 0,
            top: 0,
            bottom: 0,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: focusNode.hasFocus ? 2 : 0,
              decoration: BoxDecoration(
                color: _primaryColor,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(12.r),
                  bottomLeft: Radius.circular(12.r),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSignUpRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          "Don't have an account yet? ",
          style: TextStyle(
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
            color: _secondaryColor,
          ),
        ),
        Semantics(
          label: 'Sign up for a new account',
          button: true,
          child: GestureDetector(
            onTapDown: (_) => setState(() => _signUpPressed = true),
            onTapUp: (_) {
              setState(() => _signUpPressed = false);
              if (mounted) Navigator.pushNamed(context, '/signup');
            },
            onTapCancel: () => setState(() => _signUpPressed = false),
            child: AnimatedScale(
              scale: _signUpPressed ? 0.97 : 1.0,
              duration: const Duration(milliseconds: 150),
              child: Text(
                'Sign Up',
                style: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                  color: _primaryColor,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
