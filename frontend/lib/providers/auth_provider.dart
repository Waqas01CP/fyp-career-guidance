import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';

class AuthState {
  final String? token;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.token,
    this.isLoading = false,
    this.error,
  });

  AuthState copyWith({
    String? token,
    bool clearToken = false,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) =>
      AuthState(
        token: clearToken ? null : token ?? this.token,
        isLoading: isLoading ?? this.isLoading,
        error: clearError ? null : error ?? this.error,
      );

  bool get isAuthenticated => token != null;
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState()) {
    _restoreToken();
  }

  Future<void> _restoreToken() async {
    final token = await AuthService.getToken();
    if (token != null) {
      state = state.copyWith(token: token);
    }
  }

  Future<bool> register(
      String email, String password, String fullName) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final token = await AuthService.register(email, password, fullName);
      if (token != null) {
        state = state.copyWith(token: token, isLoading: false);
        return true;
      }
      state = state.copyWith(
        isLoading: false,
        error: 'Registration failed. Please try again.',
      );
      return false;
    } on Exception catch (e) {
      final isEmailExists = e.toString().contains('email_exists');
      state = state.copyWith(
        isLoading: false,
        error: isEmailExists
            ? 'An account with this email already exists.'
            : 'Registration failed. Please try again.',
      );
      return false;
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final token = await AuthService.login(email, password);
      if (token != null) {
        state = state.copyWith(token: token, isLoading: false);
        return true;
      }
      state = state.copyWith(
        isLoading: false,
        error: 'Invalid email or password.',
      );
      return false;
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        error: 'Could not connect. Check your internet and try again.',
      );
      return false;
    }
  }

  Future<void> logout() async {
    await AuthService.logout();
    state = const AuthState();
  }

  void handleUnauthorized() {
    AuthService.logout();
    state = const AuthState(
      error: 'Session expired — please log in again.',
    );
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(),
);
