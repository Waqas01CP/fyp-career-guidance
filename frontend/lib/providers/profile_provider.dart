import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

class ProfileState {
  final String onboardingStage;
  final String? sessionId;
  final Map<String, dynamic> riasecScores;
  final Map<String, dynamic> subjectMarks;
  final Map<String, dynamic> capabilityScores;
  final String studentMode;
  final String? educationLevel;
  final bool isLoading;
  final bool isLoaded;
  final String? error;

  const ProfileState({
    this.onboardingStage = 'not_started',
    this.sessionId,
    this.riasecScores = const {},
    this.subjectMarks = const {},
    this.capabilityScores = const {},
    this.studentMode = 'inter',
    this.educationLevel,
    this.isLoading = false,
    this.isLoaded = false,
    this.error,
  });

  ProfileState copyWith({
    String? onboardingStage,
    String? sessionId,
    Map<String, dynamic>? riasecScores,
    Map<String, dynamic>? subjectMarks,
    Map<String, dynamic>? capabilityScores,
    String? studentMode,
    String? educationLevel,
    bool? isLoading,
    bool? isLoaded,
    String? error,
    bool clearError = false,
  }) =>
      ProfileState(
        onboardingStage: onboardingStage ?? this.onboardingStage,
        sessionId: sessionId ?? this.sessionId,
        riasecScores: riasecScores ?? this.riasecScores,
        subjectMarks: subjectMarks ?? this.subjectMarks,
        capabilityScores: capabilityScores ?? this.capabilityScores,
        studentMode: studentMode ?? this.studentMode,
        educationLevel: educationLevel ?? this.educationLevel,
        isLoading: isLoading ?? this.isLoading,
        isLoaded: isLoaded ?? this.isLoaded,
        error: clearError ? null : error ?? this.error,
      );
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  ProfileNotifier() : super(const ProfileState());

  Future<void> loadProfile(String token) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await ApiService.get('/profile/me', token: token);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        state = state.copyWith(
          onboardingStage: data['onboarding_stage'] as String? ?? 'not_started',
          sessionId: data['session_id'] as String?,
          riasecScores: Map<String, dynamic>.from(
              data['riasec_scores'] as Map? ?? {}),
          subjectMarks: Map<String, dynamic>.from(
              data['subject_marks'] as Map? ?? {}),
          capabilityScores: Map<String, dynamic>.from(
              data['capability_scores'] as Map? ?? {}),
          studentMode: data['student_mode'] as String? ?? 'inter',
          educationLevel: data['education_level'] as String?,
          isLoading: false,
          isLoaded: true,
        );
      } else if (response.statusCode == 401) {
        state = state.copyWith(
          isLoading: false,
          error: 'session_expired',
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Could not load profile. Please try again.',
        );
      }
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        error: 'Could not connect. Check your internet and try again.',
      );
    }
  }

  void updateOnboardingStage(String stage) {
    state = state.copyWith(onboardingStage: stage);
  }

  void reset() {
    state = const ProfileState();
  }
}

final profileProvider =
    StateNotifierProvider<ProfileNotifier, ProfileState>(
  (ref) => ProfileNotifier(),
);
