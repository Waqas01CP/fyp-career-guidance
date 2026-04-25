import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/api_service.dart';

class GradesInputScreen extends ConsumerStatefulWidget {
  const GradesInputScreen({super.key});

  @override
  ConsumerState<GradesInputScreen> createState() => _GradesInputScreenState();
}

class _GradesInputScreenState extends ConsumerState<GradesInputScreen> {
  static const Color _primary   = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _fieldFill = Color(0xFFF2F4F6);

  static const List<Map<String, String>> _levelOptions = [
    {'label': 'Matric (Class 10)',       'value': 'matric'},
    {'label': 'Inter Part 1 (Class 11)', 'value': 'inter_part1'},
    {'label': 'Inter Part 2 (Class 12)', 'value': 'inter_part2'},
    {'label': 'Completed Inter',         'value': 'completed_inter'},
    {'label': 'O Level',                 'value': 'o_level'},
    {'label': 'A Level',                 'value': 'a_level'},
  ];

  // Dropdown values are backend-compatible; display names shown to user
  static const List<String> _streamOptions = [
    'Pre-Engineering', 'Pre-Medical', 'ICS', 'Commerce', 'Humanities',
  ];

  static const Map<String, String> _streamDisplayNames = {
    'Pre-Engineering': 'Pre-Engineering',
    'Pre-Medical':     'Pre-Medical',
    'ICS':             'ICS (Computer Science)',
    'Commerce':        'Commerce',
    'Humanities':      'Humanities',
  };

  static const List<String> _boardOptions = [
    'Karachi Board', 'Federal Board', 'AKU', 'Cambridge', 'Other',
  ];

  static const Map<String, List<String>> _streamSubjects = {
    'Pre-Engineering': ['Mathematics', 'Physics', 'Chemistry', 'English', 'Computer Science'],
    'Pre-Medical':     ['Biology', 'Chemistry', 'Physics', 'English', 'Urdu'],
    'ICS':             ['Mathematics', 'Physics', 'Computer Science', 'English', 'Urdu'],
    'Commerce':        ['Accounting', 'Economics', 'Business Studies', 'English', 'Mathematics'],
    'Humanities':      ['Urdu', 'English', 'Pakistan Studies', 'Islamiyat', 'Elective'],
  };

  final _formKey = GlobalKey<FormState>();
  String? _selectedLevel;
  String? _selectedStream;
  String? _selectedBoard;
  int?    _selectedYear;
  final Map<String, TextEditingController> _markControllers = {};
  bool _isSubmitting = false;

  bool get _showStreamBoard =>
      !['o_level', 'a_level'].contains(_selectedLevel);

  List<String> get _currentSubjects {
    if (_selectedLevel == null) return [];
    if (_selectedLevel == 'o_level' || _selectedLevel == 'a_level') {
      return _streamSubjects['Pre-Engineering']!;
    }
    return _streamSubjects[_selectedStream] ??
        _streamSubjects['Pre-Engineering']!;
  }

  @override
  void initState() {
    super.initState();
    _rebuildSubjectControllers();
  }

  void _rebuildSubjectControllers() {
    for (final c in _markControllers.values) {
      c.dispose();
    }
    _markControllers.clear();
    for (final s in _currentSubjects) {
      final ctrl = TextEditingController();
      ctrl.addListener(() => setState(() {}));
      _markControllers[s] = ctrl;
    }
  }

  double _computeAggregate() {
    final values = _markControllers.values
        .where((c) => c.text.isNotEmpty)
        .map((c) => double.tryParse(c.text) ?? 0.0)
        .toList();
    if (values.isEmpty) return 0.0;
    return values.reduce((a, b) => a + b) / values.length;
  }

  @override
  void dispose() {
    for (final c in _markControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _onSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedLevel == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select your education level.'),
          backgroundColor: Color(0xFFBA1A1A),
        ),
      );
      return;
    }

    // Correction 1: subject_marks as flat dict with lowercase keys, no 'year'
    final Map<String, dynamic> subjectMarks = {};
    for (final subject in _currentSubjects) {
      final key = subject.toLowerCase();
      subjectMarks[key] =
          double.tryParse(_markControllers[subject]?.text ?? '0') ?? 0.0;
    }

    final body = <String, dynamic>{
      'education_level': _selectedLevel!,
      'subject_marks':   subjectMarks,
      if (_showStreamBoard && _selectedStream != null) 'stream': _selectedStream!,
      if (_showStreamBoard && _selectedBoard  != null) 'board':  _selectedBoard!,
    };

    setState(() => _isSubmitting = true);
    final token = ref.read(authProvider).token;
    if (token == null) return;

    try {
      final response =
          await ApiService.post('/profile/grades', body, token: token);
      if (response.statusCode == 200) {
        await ref.read(profileProvider.notifier).loadProfile(token);
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/grades-complete');
      } else if (response.statusCode == 401) {
        ref.read(authProvider.notifier).handleUnauthorized();
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/login');
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to save grades. Try again.'),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FB),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF7F9FB),
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: _secondary),
          onPressed: () => Navigator.maybePop(context),
        ),
        title: const Text(
          'Academic Profile',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: _onSurface,
          ),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Step badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: _fieldFill,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'STEP 2 OF 3',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.1 * 9,
                      color: _secondary,
                    ),
                  ),
                ),
                const SizedBox(height: 12),

                // Title
                const Text(
                  'Academic Grades',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w700,
                    color: _onSurface,
                    letterSpacing: -0.02 * 28,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),

                const Text(
                  'Enter your subject marks to calculate eligibility at each university.',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    color: _secondary,
                    height: 1.6,
                  ),
                ),
                const SizedBox(height: 24),

                // Scan Marksheet — disabled, OCR deferred (image_picker not in pubspec)
                ElevatedButton.icon(
                  onPressed: null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF515F74),
                    minimumSize: const Size(double.infinity, 56),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  icon: const Icon(Icons.document_scanner, color: Colors.white54),
                  label: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'Scan Marksheet',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Colors.white54,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.white24,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: const Text(
                          'Soon',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            color: Colors.white70,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Form card
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(32),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x0F334155),
                        blurRadius: 40,
                        offset: Offset(0, 12),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Row 1: Education Level + Examination Year
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(child: _buildLevelDropdown()),
                          const SizedBox(width: 12),
                          Expanded(child: _buildYearDropdown()),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Row 2: Stream + Board (hidden for O/A Level)
                      Visibility(
                        visible: _showStreamBoard,
                        maintainState: true,
                        child: Column(
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(child: _buildStreamDropdown()),
                                const SizedBox(width: 12),
                                Expanded(child: _buildBoardDropdown()),
                              ],
                            ),
                            const SizedBox(height: 16),
                          ],
                        ),
                      ),

                      // Subject marks section
                      if (_currentSubjects.isNotEmpty) ...[
                        // Header row
                        Row(
                          children: [
                            const Expanded(
                              child: Text(
                                'SUBJECT',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.07 * 10,
                                  color: Color(0xFF6E7977),
                                ),
                              ),
                            ),
                            const Text(
                              'PERCENTAGE',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.07 * 10,
                                color: Color(0xFF6E7977),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),

                        // Marks rows
                        for (int i = 0; i < _currentSubjects.length; i++) ...[
                          _buildSubjectRow(_currentSubjects[i]),
                          if (i < _currentSubjects.length - 1)
                            Container(
                              height: 1,
                              color: const Color(0xFFF2F4F6),
                            ),
                        ],

                        // Aggregate row
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Overall Aggregate',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: _secondary,
                              ),
                            ),
                            Text(
                              '${_computeAggregate().toStringAsFixed(1)}%',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w800,
                                color: _primary,
                                letterSpacing: -0.02 * 18,
                              ),
                            ),
                          ],
                        ),
                      ] else ...[
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: _fieldFill,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Center(
                            child: Text(
                              'Select education level and stream to enter marks',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 13,
                                color: _secondary,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Save My Grades button
                ElevatedButton(
                  onPressed: _isSubmitting ? null : _onSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _primary,
                    minimumSize: const Size(double.infinity, 56),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    padding: const EdgeInsets.all(18),
                    shadowColor: const Color(0x40006B62),
                    elevation: 8,
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          'Save My Grades',
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
      ),
    );
  }

  Widget _buildLabelText(String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, left: 4),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.08 * 11,
          color: _secondary,
        ),
      ),
    );
  }

  InputDecoration _dropdownDecoration() {
    return InputDecoration(
      filled: true,
      fillColor: _fieldFill,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  Widget _buildLevelDropdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabelText('EDUCATION LEVEL'),
        DropdownButtonFormField<String>(
          key: ValueKey(_selectedLevel),
          initialValue: _selectedLevel,
          decoration: _dropdownDecoration(),
          isExpanded: true,
          hint: const Text(
            'Select level…',
            style: TextStyle(fontSize: 13, color: Color(0xFF6E7977)),
          ),
          items: _levelOptions
              .map((opt) => DropdownMenuItem<String>(
                    value: opt['value'],
                    child: Text(
                      opt['label']!,
                      style: const TextStyle(
                          fontSize: 13, color: _onSurface),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ))
              .toList(),
          onChanged: (v) => setState(() {
            _selectedLevel = v;
            _rebuildSubjectControllers();
          }),
          validator: (v) => v == null ? '' : null,
        ),
      ],
    );
  }

  Widget _buildYearDropdown() {
    final years = List.generate(7, (i) => 2026 - i);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabelText('EXAMINATION YEAR'),
        DropdownButtonFormField<int>(
          key: ValueKey(_selectedYear),
          initialValue: _selectedYear,
          decoration: _dropdownDecoration(),
          isExpanded: true,
          hint: const Text(
            'Year',
            style: TextStyle(fontSize: 13, color: Color(0xFF6E7977)),
          ),
          items: years
              .map((y) => DropdownMenuItem<int>(
                    value: y,
                    child: Text(
                      '$y',
                      style: const TextStyle(fontSize: 13, color: _onSurface),
                    ),
                  ))
              .toList(),
          onChanged: (v) => setState(() => _selectedYear = v),
        ),
      ],
    );
  }

  Widget _buildStreamDropdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabelText('STREAM / GROUP'),
        DropdownButtonFormField<String>(
          key: ValueKey(_selectedStream),
          initialValue: _selectedStream,
          decoration: _dropdownDecoration(),
          isExpanded: true,
          hint: const Text(
            'Stream',
            style: TextStyle(fontSize: 13, color: Color(0xFF6E7977)),
          ),
          items: _streamOptions
              .map((s) => DropdownMenuItem<String>(
                    value: s,
                    child: Text(
                      _streamDisplayNames[s] ?? s,
                      style: const TextStyle(fontSize: 13, color: _onSurface),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ))
              .toList(),
          onChanged: (v) => setState(() {
            _selectedStream = v;
            _rebuildSubjectControllers();
          }),
        ),
      ],
    );
  }

  Widget _buildBoardDropdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabelText('EXAMINATION BOARD'),
        DropdownButtonFormField<String>(
          key: ValueKey(_selectedBoard),
          initialValue: _selectedBoard,
          decoration: _dropdownDecoration(),
          isExpanded: true,
          hint: const Text(
            'Board',
            style: TextStyle(fontSize: 13, color: Color(0xFF6E7977)),
          ),
          items: _boardOptions
              .map((b) => DropdownMenuItem<String>(
                    value: b,
                    child: Text(
                      b,
                      style: const TextStyle(fontSize: 13, color: _onSurface),
                    ),
                  ))
              .toList(),
          onChanged: (v) => setState(() => _selectedBoard = v),
        ),
      ],
    );
  }

  Widget _buildSubjectRow(String subject) {
    final ctrl = _markControllers[subject]!;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Expanded(
            child: Text(
              subject,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: _onSurface,
              ),
            ),
          ),
          SizedBox(
            width: 72,
            child: TextFormField(
              controller: ctrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              textAlign: TextAlign.right,
              inputFormatters: [
                FilteringTextInputFormatter.allow(
                    RegExp(r'^\d{0,3}\.?\d{0,1}')),
              ],
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: _onSurface,
              ),
              decoration: const InputDecoration(
                border: InputBorder.none,
                hintText: '—',
                hintStyle: TextStyle(color: Color(0xFF6E7977)),
                suffixText: '%',
                suffixStyle: TextStyle(
                  fontSize: 13,
                  color: _secondary,
                ),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Required';
                final n = double.tryParse(v);
                if (n == null) return 'Invalid number';
                if (n < 0 || n > 100) return 'Must be 0–100';
                return null;
              },
            ),
          ),
        ],
      ),
    );
  }
}
