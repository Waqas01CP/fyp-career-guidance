import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../models/chat_message.dart';
import '../../providers/auth_provider.dart';
import '../../providers/chat_provider.dart';
import '../../providers/profile_provider.dart';
import '../../services/sse_service.dart';
import '../../widgets/thinking_indicator.dart';
import '../../widgets/university_card.dart';

class MainChatScreen extends ConsumerStatefulWidget {
  const MainChatScreen({super.key});

  @override
  ConsumerState<MainChatScreen> createState() => _MainChatScreenState();
}

class _MainChatScreenState extends ConsumerState<MainChatScreen> {
  // ── Colour constants (locked per DESIGN_HANDOFF Screen 12) ──────────────
  static const Color _primary = Color(0xFF006B62);
  static const Color _secondary = Color(0xFF515F74);
  static const Color _onSurface = Color(0xFF191C1E);
  static const Color _tertiary = Color(0xFF6616D7);
  static const Color _surface = Color(0xFFF7F9FB);
  static const Color _surfaceLow = Color(0xFFF2F4F6);
  static const Color _surfaceLowest = Color(0xFFFFFFFF);

  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final _inputFocusNode = FocusNode();

  StreamSubscription<Map<String, dynamic>>? _sseSubscription;
  Timer? _streamTimeout;

  // Suggested chips — shown only before any messages
  static const List<String> _suggestedChips = [
    'What universities suit me?',
    'Best CS programs in Karachi',
    'Show my recommendations',
    'What is my match score?',
  ];

  @override
  void initState() {
    super.initState();
    _inputController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _streamTimeout?.cancel();
    _sseSubscription?.cancel();
    _inputController.dispose();
    _scrollController.dispose();
    _inputFocusNode.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;

    final token = ref.read(authProvider).token;
    final sessionId = ref.read(profileProvider).sessionId;

    if (token == null || sessionId == null) {
      _handleUnauthorized();
      return;
    }

    _inputController.clear();
    _inputFocusNode.unfocus();

    // Clear previous chat recommendations and messages before a new send
    ref.read(chatProvider.notifier).reset();

    // Add user message and start AI message placeholder
    ref.read(chatProvider.notifier).addUserMessage(trimmed);
    ref.read(chatProvider.notifier).startAssistantMessage();
    _scrollToBottom();

    _streamTimeout?.cancel();
    _streamTimeout = Timer(const Duration(seconds: 90), () {
      ref.read(chatProvider.notifier).setError(
        'The response is taking too long. '
        'Please try sending your message again.'
      );
      _streamTimeout = null;
    });

    // Stream SSE events
    try {
      _sseSubscription?.cancel();
      _sseSubscription = SseService.stream(
        sessionId: sessionId,
        userInput: trimmed,
        token: token,
      ).listen(
        (event) {
          if (!mounted) return;
          final eventType = event['event'] as String? ?? '';
          final data = event['data'] as Map<String, dynamic>? ?? {};

          switch (eventType) {
            case 'status':
              final statusKey = data['status'] as String? ?? '';
              ref.read(chatProvider.notifier).updateStatus(statusKey);
            case 'chunk':
              final chunk = data['text'] as String? ?? '';
              if (chunk.isNotEmpty) {
                ref.read(chatProvider.notifier).appendChunk(chunk);
                _scrollToBottom();
              }
            case 'rich_ui':
              final uiType = data['type'] as String? ?? '';
              if (uiType == 'university_card') {
                ref.read(chatProvider.notifier).addRecommendation(data);
              } else if (uiType == 'roadmap_timeline') {
                ref.read(chatProvider.notifier).setRoadmapTimeline(data);
              }
            default:
              // Unknown event type — skip silently per CLAUDE.md
              break;
          }
        },
        onDone: () {
          _streamTimeout?.cancel();
          _streamTimeout = null;
          if (!mounted) return;
          ref.read(chatProvider.notifier).finishStreaming();
          _scrollToBottom();
        },
        onError: (Object e) {
          _streamTimeout?.cancel();
          _streamTimeout = null;
          if (!mounted) return;
          final errStr = e.toString();
          if (errStr.contains('401')) {
            _handleUnauthorized();
          } else {
            ref.read(chatProvider.notifier).setError(
                  'Could not reach AI advisor. Please try again.',
                );
          }
        },
        cancelOnError: true,
      );
    } catch (e) {
      _streamTimeout?.cancel();
      _streamTimeout = null;
      if (!mounted) return;
      ref.read(chatProvider.notifier).setError(
            'Could not reach AI advisor. Please try again.',
          );
    }
  }

  void _handleUnauthorized() {
    ref.read(authProvider.notifier).handleUnauthorized();
    if (!mounted) return;
    Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
  }

  // ── Build: AppBar ─────────────────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar(bool isStreaming) {
    return PreferredSize(
      preferredSize: Size.fromHeight(52.h),
      child: AppBar(
        backgroundColor: _primary,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: Row(
          children: [
            CircleAvatar(
              radius: 16.r,
              backgroundColor: Colors.white.withValues(alpha: 0.2),
              child: Icon(Icons.smart_toy, color: Colors.white, size: 18.r),
            ),
            SizedBox(width: 12.w),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'AI Advisor',
                  style: TextStyle(
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                Text(
                  isStreaming ? 'Thinking…' : 'Online · Ready',
                  style: TextStyle(
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w400,
                    color: Colors.white.withValues(alpha: 0.75),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'My Profile',
            icon: Icon(
              Icons.person_outline_rounded,
              size: 22.r,
              color: Colors.white,
            ),
            onPressed: () => Navigator.pushNamed(context, '/profile'),
          ),
          IconButton(
            icon: Icon(Icons.dashboard_outlined,
                color: Colors.white, size: 22.r),
            onPressed: () =>
                Navigator.pushReplacementNamed(context, '/dashboard'),
            tooltip: 'Dashboard',
          ),
          IconButton(
            icon: Icon(Icons.settings_outlined,
                color: Colors.white, size: 22.r),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
            tooltip: 'Settings',
          ),
          SizedBox(width: 4.w),
        ],
      ),
    );
  }

  // ── Build: Suggested chips ────────────────────────────────────────────────
  Widget _buildSuggestedChips() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
      child: Row(
        children: _suggestedChips
            .map((chip) => Padding(
                  padding: EdgeInsets.only(right: 8.w),
                  child: ActionChip(
                    label: Text(
                      chip,
                      style: TextStyle(
                        fontSize: 13.sp,
                        fontWeight: FontWeight.w500,
                        color: _secondary,
                      ),
                    ),
                    backgroundColor: _surfaceLow,
                    side: BorderSide.none,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20.r),
                    ),
                    onPressed: () => _sendMessage(chip),
                    padding: EdgeInsets.symmetric(
                        horizontal: 16.w, vertical: 12.h),
                  ),
                ))
            .toList(),
      ),
    );
  }

  // ── Build: Student bubble ─────────────────────────────────────────────────
  Widget _buildUserBubble(ChatMessage msg) {
    return Padding(
      padding: EdgeInsets.only(bottom: 4.h),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.75),
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
              decoration: BoxDecoration(
                color: _primary,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(18.r),
                  topRight: Radius.circular(18.r),
                  bottomLeft: Radius.circular(18.r),
                  bottomRight: Radius.circular(4.r),
                ),
              ),
              child: Text(
                msg.content,
                style: TextStyle(
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w400,
                  color: Colors.white,
                  height: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Build: AI bubble ──────────────────────────────────────────────────────
  Widget _buildAIBubble(ChatMessage msg, bool isStreaming, bool isLast, String? errorMsg) {
    final isEmpty = msg.content.isEmpty;

    if (isLast && !isStreaming && errorMsg != null) {
      return Padding(
        padding: EdgeInsets.only(bottom: 4.h),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 16.r,
              backgroundColor: const Color(0xFFFFDAD6),
              child: Icon(Icons.error_outline, size: 16.r, color: const Color(0xFFBA1A1A)),
            ),
            SizedBox(width: 8.w),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    constraints: BoxConstraints(
                        maxWidth: MediaQuery.of(context).size.width * 0.85),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFDAD6),
                      borderRadius: BorderRadius.only(
                        topLeft: Radius.circular(18.r),
                        topRight: Radius.circular(18.r),
                        bottomLeft: Radius.circular(4.r),
                        bottomRight: Radius.circular(18.r),
                      ),
                      border: const Border(
                        left: BorderSide(color: Color(0xFFBA1A1A), width: 3),
                      ),
                    ),
                    padding: EdgeInsets.all(14.r),
                    child: Text(
                      errorMsg,
                      style: TextStyle(
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w400,
                        color: const Color(0xFF93000A),
                        height: 1.6,
                      ),
                    ),
                  ),
                  SizedBox(height: 8.h),
                  ElevatedButton(
                    onPressed: () {
                      final chatState = ref.read(chatProvider);
                      // Resend the last user message
                      final lastUserMsg = chatState.messages.lastWhere((m) => m.isUser, orElse: () => ChatMessage(id: '', role: 'user', content: '', timestamp: DateTime.now()));
                      if (lastUserMsg.content.isNotEmpty) {
                        _sendMessage(lastUserMsg.content);
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12.r),
                      ),
                    ),
                    child: Text('Try Again', style: TextStyle(fontSize: 14.sp, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Padding(
      padding: EdgeInsets.only(bottom: 4.h),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // AI avatar
          CircleAvatar(
            radius: 16.r,
            backgroundColor: _surfaceLow,
            child: Icon(Icons.smart_toy, size: 16.r, color: _secondary),
          ),
          SizedBox(width: 8.w),
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.85),
              decoration: BoxDecoration(
                color: _surfaceLowest,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(18.r),
                  topRight: Radius.circular(18.r),
                  bottomLeft: Radius.circular(4.r),
                  bottomRight: Radius.circular(18.r),
                ),
                border: const Border(
                  left: BorderSide(color: _tertiary, width: 3),
                ),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x0F334155),
                    blurRadius: 16,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              padding: EdgeInsets.all(14.r),
              child: isEmpty && isStreaming
                  ? const ThinkingIndicator()
                  : Text(
                      msg.content,
                      style: TextStyle(
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w400,
                        color: _onSurface,
                        height: 1.6,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Build: Status label ───────────────────────────────────────────────────
  Widget _buildStatusLabel(String label) {
    return Padding(
      padding: EdgeInsets.only(left: 48.w, bottom: 8.h),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12.sp,
          fontWeight: FontWeight.w400,
          color: _tertiary,
          fontStyle: FontStyle.italic,
        ),
      ),
    );
  }

  // ── Build: Input bar ──────────────────────────────────────────────────────
  Widget _buildInputBar(bool isStreaming) {
    final canSend =
        _inputController.text.trim().isNotEmpty && !isStreaming;

    return Container(
      color: _surface,
      padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 16.h),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: _surfaceLow,
                  borderRadius: BorderRadius.circular(24.r),
                ),
                child: TextField(
                  controller: _inputController,
                  focusNode: _inputFocusNode,
                  maxLines: null,
                  textInputAction: TextInputAction.newline,
                  style: TextStyle(
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w400,
                    color: _onSurface,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Ask your AI advisor…',
                    hintStyle: TextStyle(
                      fontSize: 15.sp,
                      fontWeight: FontWeight.w400,
                      color: _secondary,
                    ),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(
                        horizontal: 16.w, vertical: 12.h),
                  ),
                  onSubmitted: isStreaming
                      ? null
                      : (_) => _sendMessage(_inputController.text),
                ),
              ),
            ),
            SizedBox(width: 8.w),
            GestureDetector(
              onTap: canSend
                  ? () => _sendMessage(_inputController.text)
                  : null,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 48.r,
                height: 48.r,
                decoration: BoxDecoration(
                  color: canSend
                      ? _primary
                      : const Color(0xFFE6E8EA),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.send_rounded,
                  color: canSend ? Colors.white : _secondary,
                  size: 20.r,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getMissingDataMessage(ProfileState profile) {
    if (!profile.riasecScores.isNotEmpty) {
      return 'Complete your interest profile quiz (Step 1 of 3) '
             'to get personalised degree recommendations.';
    }
    if (!profile.subjectMarks.isNotEmpty) {
      return 'Enter your academic grades (Step 2 of 3) '
             'so we can match you with eligible degrees.';
    }
    if (!profile.capabilityScores.isNotEmpty) {
      return 'Complete the capability assessment (Step 3 of 3) '
             'to finalise your profile.';
    }
    return 'Your profile is incomplete. '
           'Please complete all steps to get recommendations.';
  }

  Widget _buildProfileActionButton(
      String label, IconData icon, VoidCallback onTap) {
    return Padding(
      padding: EdgeInsets.only(bottom: 8.h),
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: Icon(icon, size: 16.r),
        label: Text(label,
          style: TextStyle(fontSize: 13.sp,
            fontWeight: FontWeight.w600)),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF006B62),
          foregroundColor: Colors.white,
          minimumSize: Size(double.infinity, 44.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10.r)),
        ),
      ),
    );
  }

  Widget _buildLockedBanner(ProfileState profile, bool hasRiasec, bool hasGrades, bool hasCapability) {
    return Container(
      padding: EdgeInsets.all(16.r),
      margin: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: const Color(0xFFEADDFF), // tertiaryFixed
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: const Color(0xFF6616D7), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(Icons.lock_outline, size: 16.r,
                 color: const Color(0xFF6616D7)),
            SizedBox(width: 8.w),
            Text('Complete your profile first',
              style: TextStyle(fontSize: 14.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF25005A))),
          ]),
          SizedBox(height: 8.h),
          Text(_getMissingDataMessage(profile),
            style: TextStyle(fontSize: 13.sp,
              color: const Color(0xFF5A00C6))),
          SizedBox(height: 12.h),
          if (!hasRiasec)
            _buildProfileActionButton(
              'Complete Interest Assessment',
              Icons.psychology_outlined,
              () => Navigator.pushNamed(context, '/riasec-quiz'),
            ),
          if (hasRiasec && !hasGrades)
            _buildProfileActionButton(
              'Enter Academic Grades',
              Icons.school_outlined,
              () => Navigator.pushNamed(context, '/grades-input'),
            ),
          if (hasRiasec && hasGrades && !hasCapability)
            _buildProfileActionButton(
              'Complete Capability Assessment',
              Icons.quiz_outlined,
              () => Navigator.pushNamed(context, '/assessment'),
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);
    final messages = chatState.messages;
    final isStreaming = chatState.isStreaming;
    final statusLabel = chatState.currentStatusLabel;
    final errorMsg = chatState.error;
    final showChips = messages.isEmpty && !isStreaming;

    final profile = ref.watch(profileProvider);
    final bool onboardingComplete = profile.onboardingStage == 'assessment_complete';
    final bool hasRiasec = profile.riasecScores.isNotEmpty;
    final bool hasGrades = profile.subjectMarks.isNotEmpty;
    final bool hasCapability = profile.capabilityScores.isNotEmpty;
    final bool profileComplete = onboardingComplete && hasRiasec && hasGrades && hasCapability;

    return Scaffold(
      backgroundColor: _surface,
      resizeToAvoidBottomInset: true,
      appBar: _buildAppBar(isStreaming),
      body: Column(
        children: [
          // ── Chat list ──────────────────────────────────────────────────
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 0),
              itemCount: messages.length + (showChips ? 1 : 0),
              itemBuilder: (context, index) {
                // First item: chips (only if no messages yet)
                if (showChips && index == 0) {
                  return Padding(
                    padding: EdgeInsets.only(bottom: 16.h),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(height: 8.h),
                        Text(
                          'How can I help you today?',
                          style: TextStyle(
                            fontSize: 18.sp,
                            fontWeight: FontWeight.w700,
                            color: _onSurface,
                            letterSpacing: -0.36,
                          ),
                        ),
                        SizedBox(height: 4.h),
                        Text(
                          'Ask about universities, programmes, or your career options.',
                          style: TextStyle(
                            fontSize: 13.sp,
                            fontWeight: FontWeight.w400,
                            color: _secondary,
                            height: 1.5,
                          ),
                        ),
                        SizedBox(height: 16.h),
                        _buildSuggestedChips(),
                      ],
                    ),
                  );
                }

                final msgIndex = showChips ? index - 1 : index;
                final msg = messages[msgIndex];
                final isLast = msgIndex == messages.length - 1;

                return Padding(
                  padding: EdgeInsets.only(
                    bottom: isLast ? 16.h : 0,
                  ),
                  child: Column(
                    children: [
                      if (msg.isUser)
                        _buildUserBubble(msg)
                      else
                        _buildAIBubble(msg, isStreaming, isLast, errorMsg),
                      
                      // Status label — show below last AI bubble when streaming
                      if (!msg.isUser &&
                          isLast &&
                          isStreaming &&
                          statusLabel != null)
                        _buildStatusLabel(statusLabel),
                        
                      // Recommendation cards
                      if (!msg.isUser && isLast && chatState.recommendations.isNotEmpty && !isStreaming)
                        ListView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: chatState.recommendations.length,
                          itemBuilder: (ctx, i) => UniversityCard(
                            recommendation: chatState.recommendations[i],
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),

          // ── Suggested chips row (only when list is empty) ──────────────
          // (chips rendered inline in ListView when showChips=true above)

          // ── Input bar / Locked banner ──────────────────────────────────
          if (!profileComplete)
            _buildLockedBanner(profile, hasRiasec, hasGrades, hasCapability)
          else
            _buildInputBar(isStreaming),
        ],
      ),
    );
  }
}
