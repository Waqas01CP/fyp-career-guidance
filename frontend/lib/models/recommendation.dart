/// Recommendation — mirrors a single entry in roadmap_snapshot (15 fields)
/// plus the extra university_card display fields (rank, field_id, lifecycle_status, etc.)
/// See Point 3 roadmap_snapshot schema and Point 5 university_card payload.
/// Implement full fromJson factory in Sprint 3.
class Recommendation {
  final int rank;
  final String degreeId;
  final String degreeName;
  final String universityId;
  final String universityName;
  final String fieldId;
  final double totalScore;
  final double matchScoreNormalised;
  final double futureScore;
  final String meritTier;
  final String eligibilityTier;
  final String? eligibilityNote;
  final double feePerSemester;
  final double aggregateUsed;
  final List<String> softFlags;
  final String lifecycleStatus;
  final double riskFactor;
  final int? rozeeLiveCount;
  final bool policyPendingVerification;

  const Recommendation({
    required this.rank,
    required this.degreeId,
    required this.degreeName,
    required this.universityId,
    required this.universityName,
    required this.fieldId,
    required this.totalScore,
    required this.matchScoreNormalised,
    required this.futureScore,
    required this.meritTier,
    required this.eligibilityTier,
    this.eligibilityNote,
    required this.feePerSemester,
    required this.aggregateUsed,
    required this.softFlags,
    required this.lifecycleStatus,
    required this.riskFactor,
    this.rozeeLiveCount,
    required this.policyPendingVerification,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      rank: json['rank'] as int,
      degreeId: json['degree_id'] as String,
      degreeName: json['degree_name'] as String,
      universityId: json['university_id'] as String,
      universityName: json['university_name'] as String,
      fieldId: json['field_id'] as String,
      totalScore: (json['total_score'] as num).toDouble(),
      matchScoreNormalised: (json['match_score_normalised'] as num).toDouble(),
      futureScore: (json['future_score'] as num).toDouble(),
      meritTier: json['merit_tier'] as String,
      eligibilityTier: json['eligibility_tier'] as String,
      eligibilityNote: json['eligibility_note'] as String?,
      feePerSemester: (json['fee_per_semester'] as num).toDouble(),
      aggregateUsed: (json['aggregate_used'] as num).toDouble(),
      softFlags: List<String>.from(json['soft_flags'] as List? ?? []),
      lifecycleStatus: json['lifecycle_status'] as String,
      riskFactor: (json['risk_factor'] as num).toDouble(),
      rozeeLiveCount: json['rozee_live_count'] as int?,
      policyPendingVerification: json['policy_pending_verification'] as bool,
    );
  }
}
