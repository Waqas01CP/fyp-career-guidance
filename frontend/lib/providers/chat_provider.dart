import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat_message.dart';
import '../models/recommendation.dart';

// Status label mapping — matches backend NODE_STATUS_MAP
const Map<String, String> kStatusLabels = {
  'profiling':              'Analysing your profile...',
  'filtering_degrees':      'Checking your eligibility...',
  'scoring_degrees':        'Ranking your options...',
  'generating_explanation': 'Preparing your recommendations...',
  'fetching_fees':          'Looking up fees...',
  'fetching_market_data':   'Checking market data...',
  'done':                   '',
};

class ChatState {
  final List<ChatMessage> messages;
  final List<Recommendation> recommendations;
  final Map<String, dynamic>? roadmapTimeline;
  final String? currentStatusLabel;
  final bool isStreaming;
  final String? error;

  const ChatState({
    this.messages = const [],
    this.recommendations = const [],
    this.roadmapTimeline,
    this.currentStatusLabel,
    this.isStreaming = false,
    this.error,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    List<Recommendation>? recommendations,
    Map<String, dynamic>? roadmapTimeline,
    String? currentStatusLabel,
    bool clearStatus = false,
    bool? isStreaming,
    String? error,
    bool clearError = false,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        recommendations: recommendations ?? this.recommendations,
        roadmapTimeline: roadmapTimeline ?? this.roadmapTimeline,
        currentStatusLabel:
            clearStatus ? null : currentStatusLabel ?? this.currentStatusLabel,
        isStreaming: isStreaming ?? this.isStreaming,
        error: clearError ? null : error ?? this.error,
      );
}

class ChatNotifier extends StateNotifier<ChatState> {
  ChatNotifier() : super(const ChatState());

  void addUserMessage(String content) {
    final msg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'user',
      content: content,
      timestamp: DateTime.now(),
    );
    state = state.copyWith(
      messages: [...state.messages, msg],
    );
  }

  void startAssistantMessage() {
    final msg = ChatMessage(
      id: 'streaming_${DateTime.now().millisecondsSinceEpoch}',
      role: 'assistant',
      content: '',
      timestamp: DateTime.now(),
    );
    state = state.copyWith(
      messages: [...state.messages, msg],
      isStreaming: true,
      clearError: true,
    );
  }

  void appendChunk(String chunk) {
    if (state.messages.isEmpty) return;
    final msgs = List<ChatMessage>.from(state.messages);
    final last = msgs.last;
    msgs[msgs.length - 1] = ChatMessage(
      id: last.id,
      role: last.role,
      content: last.content + chunk,
      timestamp: last.timestamp,
    );
    state = state.copyWith(messages: msgs);
  }

  void updateStatus(String statusKey) {
    final label = kStatusLabels[statusKey] ?? '';
    state = state.copyWith(
      currentStatusLabel: label.isEmpty ? null : label,
      clearStatus: label.isEmpty,
    );
  }

  void addRecommendation(Map<String, dynamic> payload) {
    try {
      final rec = Recommendation.fromJson(payload);
      state = state.copyWith(
        recommendations: [...state.recommendations, rec],
      );
    } catch (_) {
      // Malformed payload — skip silently, do not crash
    }
  }

  void setRoadmapTimeline(Map<String, dynamic> payload) {
    state = state.copyWith(roadmapTimeline: payload);
  }

  void setRecommendations(List<Recommendation> recs) {
    state = state.copyWith(recommendations: recs);
  }

  void finishStreaming() {
    state = state.copyWith(
      isStreaming: false,
      clearStatus: true,
    );
  }

  void setError(String error) {
    state = state.copyWith(
      isStreaming: false,
      clearStatus: true,
      error: error,
    );
  }

  void reset() {
    state = const ChatState();
  }
}

final chatProvider =
    StateNotifierProvider<ChatNotifier, ChatState>(
  (ref) => ChatNotifier(),
);
