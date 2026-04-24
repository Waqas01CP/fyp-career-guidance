/// ChatMessage — a single message in the chat UI.
/// role: 'user' | 'assistant'
/// id is generated client-side — never read from backend JSON.
class ChatMessage {
  final String id;
  final String role;
  final String content;
  final DateTime timestamp;

  const ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: json['role'] as String,
      content: json['content'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';
}
