import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Base HTTP client. All API calls go through this.
/// Base URL: set in CLAUDE.md / environment config.
///
/// Both methods enforce a 30-second timeout. When the Render backend is
/// sleeping (free-tier cold start ~50 s), requests fail with a
/// TimeoutException after 30 s instead of hanging indefinitely. The
/// TimeoutException propagates into the existing catch(_) blocks in each
/// screen, showing the "No connection. Check your internet." snackbar and
/// re-enabling any submit button, so the user can retry once the server warms.
class ApiService {
  static const String baseUrl = 'https://fyp-career-guidance-api.onrender.com/api/v1';
  static const Duration _timeout = Duration(seconds: 30);

  static Map<String, String> _headers(String? token) => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  static Future<http.Response> get(String path, {String? token}) async {
    return http
        .get(Uri.parse('$baseUrl$path'), headers: _headers(token))
        .timeout(_timeout);
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body, {String? token}) async {
    return http
        .post(
          Uri.parse('$baseUrl$path'),
          headers: _headers(token),
          body: jsonEncode(body),
        )
        .timeout(_timeout);
  }
}
