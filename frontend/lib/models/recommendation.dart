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
  final String riskFactor;
  final int? rozeeLiveCount;
  final String? rozeeLastUpdated;
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
    this.rozeeLastUpdated,
    required this.policyPendingVerification,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      // Use (as num).toInt() everywhere an int is expected —
      // some backends emit rank/count as double (e.g. 1.0 instead of 1).
      rank: (json['rank'] as num).toInt(),
      degreeId: json['degree_id'] as String,
      degreeName: json['degree_name'] as String,
      universityId: json['university_id'] as String,
      universityName: json['university_name'] as String,
      fieldId: json['field_id'] as String? ?? '',
      totalScore: (json['total_score'] as num).toDouble(),
      matchScoreNormalised: (json['match_score_normalised'] as num).toDouble(),
      futureScore: (json['future_score'] as num? ?? 0).toDouble(),
      meritTier: json['merit_tier'] as String? ?? 'Unknown',
      eligibilityTier: json['eligibility_tier'] as String? ?? 'Unknown',
      eligibilityNote: json['eligibility_note'] as String?,
      feePerSemester: (json['fee_per_semester'] as num? ?? 0).toDouble(),
      aggregateUsed: (json['aggregate_used'] as num? ?? 0).toDouble(),
      softFlags: List<String>.from(json['soft_flags'] as List? ?? []),
      lifecycleStatus: json['lifecycle_status'] as String? ?? 'active',
      riskFactor: json['risk_factor'] as String? ?? 'Low',
      // int? fields — backend may send as double or null
      rozeeLiveCount: json['rozee_live_count'] == null
          ? null
          : (json['rozee_live_count'] as num).toInt(),
      rozeeLastUpdated: json['rozee_last_updated'] as String?,
      // bool field — guard against null or non-bool values from backend
      policyPendingVerification:
          json['policy_pending_verification'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'rank': rank,
      'degree_id': degreeId,
      'degree_name': degreeName,
      'university_id': universityId,
      'university_name': universityName,
      'field_id': fieldId,
      'total_score': totalScore,
      'match_score_normalised': matchScoreNormalised,
      'future_score': futureScore,
      'merit_tier': meritTier,
      'eligibility_tier': eligibilityTier,
      'eligibility_note': eligibilityNote,
      'fee_per_semester': feePerSemester,
      'aggregate_used': aggregateUsed,
      'soft_flags': softFlags,
      'lifecycle_status': lifecycleStatus,
      'risk_factor': riskFactor,
      'rozee_live_count': rozeeLiveCount,
      'rozee_last_updated': rozeeLastUpdated,
      'policy_pending_verification': policyPendingVerification,
    };
  }
}
