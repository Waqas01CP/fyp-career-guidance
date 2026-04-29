import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/recommendation.dart';

class RecommendationCacheService {
  static const _storage = FlutterSecureStorage();
  static const _key = 'last_recommendations';

  static Future<void> save(List<Recommendation> recommendations) async {
    try {
      final List<Map<String, dynamic>> rawList = recommendations.map((r) => r.toJson()).toList();
      final data = jsonEncode(rawList);
      await _storage.write(key: _key, value: data);
    } catch (e) {
      debugPrint('Failed to save recommendations to cache: $e');
    }
  }

  static Future<List<Recommendation>?> load() async {
    try {
      final data = await _storage.read(key: _key);
      if (data != null) {
        final List<dynamic> rawList = jsonDecode(data);
        return rawList.map((json) => Recommendation.fromJson(json as Map<String, dynamic>)).toList();
      }
    } catch (e) {
      debugPrint('Failed to load recommendations from cache: $e');
    }
    return null;
  }
}
