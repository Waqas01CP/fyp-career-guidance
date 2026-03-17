import 'dart:convert';
import 'package:http/http.dart' as http;

/// Base HTTP client. All API calls go through this.
/// Base URL: set in CLAUDE.md / environment config.
class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  static Map<String, String> _headers(String? token) => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  static Future<http.Response> get(String path, {String? token}) async {
    return http.get(Uri.parse('$baseUrl$path'), headers: _headers(token));
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body, {String? token}) async {
    return http.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers(token),
      body: jsonEncode(body),
    );
  }
}
