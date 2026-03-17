import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_service.dart';

/// SSE stream parser for POST /api/v1/chat/stream.
/// Parses three event types: status, chunk, rich_ui.
/// Do NOT use dio — use http with streaming response parser.
class SseService {
  /// Stream SSE events from the chat endpoint.
  /// Yields maps with keys: event (String) and data (Map).
  /// Throws [Exception] if the server returns a non-200 status.
  static Stream<Map<String, dynamic>> stream({
    required String sessionId,
    required String userInput,
    required String token,
    Map<String, dynamic> contextOverrides = const {},
  }) async* {
    final request = http.Request('POST', Uri.parse('${ApiService.baseUrl}/chat/stream'));
    request.headers['Authorization'] = 'Bearer $token';
    request.headers['Content-Type'] = 'application/json';
    request.body = jsonEncode({
      'session_id': sessionId,
      'user_input': userInput,
      'context_overrides': contextOverrides,
    });

    final client = http.Client();
    try {
      final streamedResponse = await client.send(request);

      // Check status before attempting to parse SSE stream
      if (streamedResponse.statusCode != 200) {
        final body = await streamedResponse.stream.bytesToString();
        throw Exception(
          'Chat stream failed with status ${streamedResponse.statusCode}: $body',
        );
      }

      String currentEvent = '';
      await for (final line in streamedResponse.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter())) {
        if (line.startsWith('event:')) {
          currentEvent = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          final rawData = line.substring(5).trim();
          try {
            final data = jsonDecode(rawData) as Map<String, dynamic>;
            yield {'event': currentEvent, 'data': data};
          } catch (_) {
            // Malformed JSON — skip silently
          }
        }
      }
    } finally {
      client.close();
    }
  }
}
