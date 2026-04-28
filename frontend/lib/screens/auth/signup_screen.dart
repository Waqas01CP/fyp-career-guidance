import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/auth_provider.dart';

class SignupScreen extends ConsumerStatefulWidget {
  const SignupScreen({super.key});

  @override
  ConsumerState<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends ConsumerState<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  final _firstNameFocus = FocusNode();
  final _lastNameFocus = FocusNode();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();
  final _confirmFocus = FocusNode();

  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  bool _isLoading = false;
  bool _submitPressed = false;
  bool _hasMinLength = false;
  bool _hasNumber = false;
  bool _hasUppercase = false;

  static const Color _bgColor       = Color(0xFFF7F9FB);
  static const Color _primaryColor   = Color(0xFF006B62);
  static const Color _gradientEnd    = Color(0xFF00857A);
  static const Color _fieldFill      = Color(0xFFF2F4F6);
  static const Color _secondaryColor = Color(0xFF515F74);
  static const Color _onSurface      = Color(0xFF191C1E);

  @override
  void initState() {
    super.initState();
    for (final node in [
      _firstNameFocus,
      _lastNameFocus,
      _emailFocus,
      _passwordFocus,
      _confirmFocus,
    ]) {
      node.addListener(() => setState(() {}));
    }
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _firstNameFocus.dispose();
    _lastNameFocus.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    _confirmFocus.dispose();
    super.dispose();
  }

  Future<void> _onSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    final fullName =
        '${_firstNameController.text.trim()} ${_lastNameController.text.trim()}';
    final success = await ref.read(authProvider.notifier).register(
          _emailController.text.trim(),
          _passwordController.text,
          fullName,
        );
    if (!mounted) return;
    if (success) {
      Navigator.pushReplacementNamed(context, '/riasec-quiz');
    } else {
      setState(() => _isLoading = false);
    }
  }

  Widget _buildField({
    required TextEditingController controller,
    required FocusNode focusNode,
    required String label,
    IconData? prefixIcon,
    TextInputType keyboardType = TextInputType.text,
    TextInputAction textInputAction = TextInputAction.next,
    List<String>? autofillHints,
    bool obscureText = false,
    Widget? suffixIcon,
    String? Function(String?)? validator,
    void Function(String)? onChanged,
  }) {
    return Stack(
      children: [
        TextFormField(
          controller: controller,
          focusNode: focusNode,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          autofillHints: autofillHints,
          obscureText: obscureText,
          onChanged: onChanged,
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
            prefixIcon: prefixIcon != null
                ? Icon(prefixIcon, color: _secondaryColor, size: 20.r)
                : null,
            suffixIcon: suffixIcon,
            contentPadding:
                EdgeInsets.symmetric(horizontal: 16.w, vertical: 18.h),
          ),
          validator: validator,
        ),
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
    );
  }

  Widget _buildRule(String label, bool passes) {
    return Row(
      children: [
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: Icon(
            passes ? Icons.check_circle : Icons.radio_button_unchecked,
            key: ValueKey(passes),
            size: 16.r,
            color: passes ? _primaryColor : _secondaryColor,
          ),
        ),
        SizedBox(width: 8.w),
        Text(
          label,
          style: TextStyle(
            fontSize: 11.sp,
            fontWeight: FontWeight.w400,
            color: _secondaryColor,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
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
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isCompact = MediaQuery.of(context).size.height < 600;
            final vGap = isCompact ? 10.h : 16.h;
            final cardPadding = isCompact ? 16.r : 24.r;
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
                      bottom: 24.h,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _buildGradientBar(),
                        _buildFormCard(cardPadding),
                        SizedBox(height: vGap),
                        _buildSignInRow(),
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
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.all(Radius.circular(32)),
        boxShadow: [
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
            Text(
              'Create Account',
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.w700,
                color: _onSurface,
                letterSpacing: -0.56,
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              'Fill in your details to begin your guided experience.',
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
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // First name / Last name two-column row
                  Row(
                    children: [
                      Expanded(
                        child: _buildField(
                          controller: _firstNameController,
                          focusNode: _firstNameFocus,
                          label: 'First Name',
                          prefixIcon: Icons.person,
                          textInputAction: TextInputAction.next,
                          autofillHints: const [AutofillHints.givenName],
                          validator: (v) =>
                              v == null || v.trim().isEmpty ? 'Required' : null,
                        ),
                      ),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: _buildField(
                          controller: _lastNameController,
                          focusNode: _lastNameFocus,
                          label: 'Last Name',
                          prefixIcon: Icons.person,
                          textInputAction: TextInputAction.next,
                          autofillHints: const [AutofillHints.familyName],
                          validator: (v) =>
                              v == null || v.trim().isEmpty ? 'Required' : null,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 16.h),
                  _buildField(
                    controller: _emailController,
                    focusNode: _emailFocus,
                    label: 'Email Address',
                    prefixIcon: Icons.mail,
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
                    prefixIcon: Icons.lock,
                    textInputAction: TextInputAction.next,
                    autofillHints: const [AutofillHints.newPassword],
                    obscureText: _obscurePassword,
                    suffixIcon: IconButton(
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
                    onChanged: (value) {
                      setState(() {
                        _hasMinLength = value.length >= 8;
                        _hasNumber = value.contains(RegExp(r'[0-9]'));
                        _hasUppercase = value.contains(RegExp(r'[A-Z]'));
                      });
                    },
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      if (v.length < 8) return 'Min 8 characters';
                      return null;
                    },
                  ),
                  SizedBox(height: 8.h),
                  _buildField(
                    controller: _confirmPasswordController,
                    focusNode: _confirmFocus,
                    label: 'Confirm Password',
                    prefixIcon: Icons.verified_user,
                    textInputAction: TextInputAction.done,
                    autofillHints: const [AutofillHints.newPassword],
                    obscureText: _obscureConfirm,
                    suffixIcon: IconButton(
                      onPressed: () =>
                          setState(() => _obscureConfirm = !_obscureConfirm),
                      icon: Icon(
                        _obscureConfirm
                            ? Icons.visibility_off
                            : Icons.visibility,
                        color: _secondaryColor,
                        size: 20.r,
                      ),
                    ),
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      if (v != _passwordController.text) {
                        return 'Passwords do not match';
                      }
                      return null;
                    },
                  ),
                  SizedBox(height: 16.h),
                  // Password rule indicators
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildRule('At least 8 characters', _hasMinLength),
                      SizedBox(height: 6.h),
                      _buildRule('One number', _hasNumber),
                      SizedBox(height: 6.h),
                      _buildRule('One uppercase letter', _hasUppercase),
                    ],
                  ),
                ],
              ),
            ),
            SizedBox(height: 24.h),
            // Create Account button with 0.97 scale press animation (Task 5a)
            Semantics(
              label: 'Create account',
              button: true,
              child: GestureDetector(
                onTapDown: (_) => setState(() => _submitPressed = true),
                onTapUp: (_) => setState(() => _submitPressed = false),
                onTapCancel: () => setState(() => _submitPressed = false),
                child: AnimatedScale(
                  scale: _submitPressed ? 0.97 : 1.0,
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
                            'Create Account',
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
            // Errors shown via SnackBar via ref.listen above—not inline
          ],
        ),
      ),
    );
  }

  Widget _buildSignInRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'Already have an account? ',
          style: TextStyle(
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
            color: _secondaryColor,
          ),
        ),
        GestureDetector(
          onTap: () {
            if (!mounted) return;
            Navigator.pushReplacementNamed(context, '/login');
          },
          child: Text(
            'Sign In',
            style: TextStyle(
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
              color: _primaryColor,
            ),
          ),
        ),
      ],
    );
  }
}
