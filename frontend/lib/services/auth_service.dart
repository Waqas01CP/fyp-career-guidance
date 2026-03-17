import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

/// Handles login, register, and JWT token storage.
/// Token stored securely via flutter_secure_storage.
class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'access_token';

  static Future<String?> register(String email, String password) async {
    final response = await ApiService.post('/auth/register', {
      'email': email,
      'password': password,
    });
    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      final token = data['access_token'] as String;
      await _storage.write(key: _tokenKey, value: token);
      return token;
    }
    return null;
  }

  static Future<String?> login(String email, String password) async {
    final response = await ApiService.post('/auth/login', {
      'email': email,
      'password': password,
    });
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final token = data['access_token'] as String;
      await _storage.write(key: _tokenKey, value: token);
      return token;
    }
    return null;
  }

  static Future<String?> getToken() => _storage.read(key: _tokenKey);
  static Future<void> logout() => _storage.delete(key: _tokenKey);
}
