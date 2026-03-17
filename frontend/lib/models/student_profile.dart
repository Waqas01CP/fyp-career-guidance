/// StudentProfile — mirrors ProfileOut from backend.
/// See schemas/profile.py ProfileOut for field definitions.
/// Implement with fromJson factory in Sprint 2.
class StudentProfile {
  final String id;
  final String onboardingStage;
  final String? educationLevel;
  final String? studentMode;
  final String? gradeSystem;
  final String? stream;
  final String? board;
  final Map<String, dynamic> riasecScores;
  final Map<String, dynamic> subjectMarks;
  final Map<String, dynamic> capabilityScores;
  final int? budgetPerSemester;
  final bool? transportWilling;
  final int? homeZone;
  final List<dynamic> statedPreferences;
  final String? familyConstraints;
  final String? careerGoal;
  final String? studentNotes;
  final DateTime updatedAt;

  const StudentProfile({
    required this.id,
    required this.onboardingStage,
    this.educationLevel,
    this.studentMode,
    this.gradeSystem,
    this.stream,
    this.board,
    required this.riasecScores,
    required this.subjectMarks,
    required this.capabilityScores,
    this.budgetPerSemester,
    this.transportWilling,
    this.homeZone,
    required this.statedPreferences,
    this.familyConstraints,
    this.careerGoal,
    this.studentNotes,
    required this.updatedAt,
  });

  factory StudentProfile.fromJson(Map<String, dynamic> json) {
    return StudentProfile(
      id: json['id'] as String,
      onboardingStage: json['onboarding_stage'] as String,
      educationLevel: json['education_level'] as String?,
      studentMode: json['student_mode'] as String?,
      gradeSystem: json['grade_system'] as String?,
      stream: json['stream'] as String?,
      board: json['board'] as String?,
      riasecScores: Map<String, dynamic>.from(json['riasec_scores'] as Map? ?? {}),
      subjectMarks: Map<String, dynamic>.from(json['subject_marks'] as Map? ?? {}),
      capabilityScores: Map<String, dynamic>.from(json['capability_scores'] as Map? ?? {}),
      budgetPerSemester: json['budget_per_semester'] as int?,
      transportWilling: json['transport_willing'] as bool?,
      homeZone: json['home_zone'] as int?,
      statedPreferences: List<dynamic>.from(json['stated_preferences'] as List? ?? []),
      familyConstraints: json['family_constraints'] as String?,
      careerGoal: json['career_goal'] as String?,
      studentNotes: json['student_notes'] as String?,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
