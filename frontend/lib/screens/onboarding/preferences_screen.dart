import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/api_service.dart';

class PreferencesScreen extends ConsumerStatefulWidget {
  const PreferencesScreen({super.key});

  @override
  ConsumerState<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends ConsumerState<PreferencesScreen> {
  bool _isLoading = false;

  final _budgetController = TextEditingController();
  final _careerController = TextEditingController();
  int? _selectedZone;
  bool? _transportWilling;

  static const List<Map<String, dynamic>> _zoneOptions = [
    {'label': 'Central Karachi (Saddar, Lyari, Keamari)', 'value': 1},
    {'label': 'East Karachi (Gulshan, Korangi, Malir)', 'value': 2},
    {'label': 'West Karachi (SITE, Orangi, Baldia)', 'value': 3},
    {'label': 'North Karachi (Surjani, Qasba, North Nazimabad)', 'value': 4},
    {'label': 'South Karachi (Clifton, DHA, Saddar South)', 'value': 5},
  ];

  @override
  void dispose() {
    _budgetController.dispose();
    _careerController.dispose();
    super.dispose();
  }

  Future<void> _submitOrSkip({required bool skip}) async {
    final budgetStr = _budgetController.text.trim();
    final budget = budgetStr.isNotEmpty ? int.tryParse(budgetStr) : null;
    final career = _careerController.text.trim().isNotEmpty ? _careerController.text.trim() : null;
    
    final bool hasData = budget != null || _selectedZone != null || _transportWilling != null || career != null;

    if (skip || !hasData) {
      Navigator.pushNamedAndRemoveUntil(context, '/chat', (route) => false);
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final token = ref.read(authProvider).token;
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final payload = {
        'budget_per_semester': budget,
        'transport_willing': _transportWilling,
        'home_zone': _selectedZone,
        'career_goal': career,
      };

      final response = await ApiService.post('/profile/preferences', payload, token: token);
      
      if (response.statusCode == 200) {
        await ref.read(profileProvider.notifier).loadProfile(token);
        if (!mounted) return;
        Navigator.pushNamedAndRemoveUntil(context, '/chat', (route) => false);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save preferences. Please try again.')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Network error. Please try again.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: EdgeInsets.only(bottom: 8.h, left: 4.w),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          fontSize: 11.sp,
          fontWeight: FontWeight.w600,
          color: const Color(0xFF515F74),
          letterSpacing: 0.8,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FB),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF7F9FB),
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 16.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Step 4 of 4 — Your Preferences',
                style: TextStyle(
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF515F74),
                ),
              ),
              SizedBox(height: 8.h),
              Text(
                'Tell us more about what you want',
                style: TextStyle(
                  fontSize: 28.sp,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF191C1E),
                  letterSpacing: -0.56,
                ),
              ),
              SizedBox(height: 32.h),

              Container(
                padding: EdgeInsets.all(24.r),
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
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Budget Input
                    _buildLabel('Budget per semester (PKR)'),
                    TextField(
                      controller: _budgetController,
                      keyboardType: TextInputType.number,
                      style: TextStyle(fontSize: 15.sp, color: const Color(0xFF191C1E)),
                      decoration: InputDecoration(
                        hintText: 'e.g. 50000',
                        hintStyle: TextStyle(color: const Color(0xFFBDC9C6)),
                        suffixText: 'PKR per semester',
                        suffixStyle: TextStyle(fontSize: 13.sp, color: const Color(0xFF515F74)),
                        filled: true,
                        fillColor: const Color(0xFFF2F4F6),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12.r),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: EdgeInsets.all(16.r),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.only(top: 4.h, left: 4.w, bottom: 24.h),
                      child: Text(
                        'Leave empty if unsure',
                        style: TextStyle(fontSize: 12.sp, color: const Color(0xFF515F74)),
                      ),
                    ),

                    // Home Zone Dropdown
                    _buildLabel('Home Zone (Karachi)'),
                    DropdownButtonFormField<int>(
                      initialValue: _selectedZone,
                      isExpanded: true,
                      icon: Icon(Icons.keyboard_arrow_down, color: const Color(0xFF515F74), size: 20.r),
                      style: TextStyle(fontSize: 15.sp, color: const Color(0xFF191C1E)),
                      decoration: InputDecoration(
                        hintText: 'Select your area',
                        hintStyle: TextStyle(color: const Color(0xFFBDC9C6)),
                        filled: true,
                        fillColor: const Color(0xFFF2F4F6),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12.r),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: EdgeInsets.all(16.r),
                      ),
                      items: _zoneOptions.map((zone) {
                        return DropdownMenuItem<int>(
                          value: zone['value'] as int,
                          child: Text(
                            zone['label'] as String,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontSize: 14.sp),
                          ),
                        );
                      }).toList(),
                      onChanged: (val) => setState(() => _selectedZone = val),
                    ),
                    SizedBox(height: 24.h),

                    // Transport Willingness
                    _buildLabel('Transport Willingness'),
                    GestureDetector(
                      onTap: () => setState(() => _transportWilling = true),
                      child: Container(
                        padding: EdgeInsets.all(16.r),
                        decoration: BoxDecoration(
                          color: _transportWilling == true ? const Color(0xFF006B62).withValues(alpha: 0.1) : const Color(0xFFF2F4F6),
                          borderRadius: BorderRadius.circular(12.r),
                          border: _transportWilling == true ? Border.all(color: const Color(0xFF006B62), width: 2) : Border.all(color: Colors.transparent, width: 2),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.directions_bus_outlined, size: 20.r, color: _transportWilling == true ? const Color(0xFF006B62) : const Color(0xFF515F74)),
                            SizedBox(width: 12.w),
                            Expanded(
                              child: Text(
                                'I can travel anywhere in Karachi',
                                style: TextStyle(
                                  fontSize: 14.sp,
                                  fontWeight: _transportWilling == true ? FontWeight.w600 : FontWeight.w400,
                                  color: _transportWilling == true ? const Color(0xFF006B62) : const Color(0xFF191C1E),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    SizedBox(height: 8.h),
                    GestureDetector(
                      onTap: () => setState(() => _transportWilling = false),
                      child: Container(
                        padding: EdgeInsets.all(16.r),
                        decoration: BoxDecoration(
                          color: _transportWilling == false ? const Color(0xFF006B62).withValues(alpha: 0.1) : const Color(0xFFF2F4F6),
                          borderRadius: BorderRadius.circular(12.r),
                          border: _transportWilling == false ? Border.all(color: const Color(0xFF006B62), width: 2) : Border.all(color: Colors.transparent, width: 2),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.home_outlined, size: 20.r, color: _transportWilling == false ? const Color(0xFF006B62) : const Color(0xFF515F74)),
                            SizedBox(width: 12.w),
                            Expanded(
                              child: Text(
                                'I prefer universities near my area',
                                style: TextStyle(
                                  fontSize: 14.sp,
                                  fontWeight: _transportWilling == false ? FontWeight.w600 : FontWeight.w400,
                                  color: _transportWilling == false ? const Color(0xFF006B62) : const Color(0xFF191C1E),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    SizedBox(height: 24.h),

                    // Career Goal Input
                    _buildLabel('Career Goal (Optional)'),
                    TextField(
                      controller: _careerController,
                      style: TextStyle(fontSize: 15.sp, color: const Color(0xFF191C1E)),
                      decoration: InputDecoration(
                        hintText: 'e.g. Software Engineer, Doctor, Business',
                        hintStyle: TextStyle(color: const Color(0xFFBDC9C6)),
                        filled: true,
                        fillColor: const Color(0xFFF2F4F6),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12.r),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: EdgeInsets.all(16.r),
                      ),
                    ),
                    SizedBox(height: 32.h),

                    // Submit Button
                    ElevatedButton(
                      onPressed: _isLoading ? null : () => _submitOrSkip(skip: false),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF006B62),
                        foregroundColor: Colors.white,
                        minimumSize: Size(double.infinity, 56.h),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16.r),
                        ),
                        elevation: 0,
                      ),
                      child: _isLoading
                          ? SizedBox(
                              width: 24.r,
                              height: 24.r,
                              child: const CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : Text(
                              'All Done!',
                              style: TextStyle(
                                fontSize: 15.sp,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                    ),
                    SizedBox(height: 16.h),
                    
                    // Skip Button
                    Center(
                      child: TextButton(
                        onPressed: _isLoading ? null : () => _submitOrSkip(skip: true),
                        style: TextButton.styleFrom(
                          minimumSize: Size(100.w, 48.h),
                        ),
                        child: Text(
                          'Skip for now',
                          style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF515F74),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
