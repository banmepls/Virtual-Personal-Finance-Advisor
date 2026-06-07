import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  /// Base URL resolution order:
  /// 1. --dart-define=API_BASE_URL=...  (covers Android emulator, staging, etc.)
  /// 2. localhost (web / iOS simulator / desktop)
  static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL');
    if (fromEnv.isNotEmpty) return fromEnv;
    // Fallback to PC's local network IP for physical Android device
    return 'http://192.168.1.15:8001/api/v1';
  }

  String? _token;
  int? userId;
  String? username;

  bool get isLoggedIn => _token != null;

  void setToken(String token) {
    _token = token;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  // ── Auth ──────────────────────────────────────────────────────────────────
  /// Decode the JWT payload to extract user id (`sub`) and `username`.
  void _decodeToken(String token) {
    _token = token;
    try {
      final parts = token.split('.');
      if (parts.length >= 2) {
        var payload = parts[1];
        payload += '=' * ((4 - payload.length % 4) % 4);
        final map =
            jsonDecode(utf8.decode(base64Url.decode(payload))) as Map<String, dynamic>;
        userId = int.tryParse(map['sub']?.toString() ?? '');
        username = map['username']?.toString();
      }
    } catch (_) {/* non-fatal */}
  }

  Future<void> _persistSession() async {
    final prefs = await SharedPreferences.getInstance();
    if (_token != null) await prefs.setString('auth_token', _token!);
    if (userId != null) await prefs.setInt('user_id', userId!);
    if (username != null) await prefs.setString('username', username!);
  }

  /// Restore a previous session from disk (called at app startup).
  Future<void> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final t = prefs.getString('auth_token');
    if (t != null && t.isNotEmpty) {
      _token = t;
      userId = prefs.getInt('user_id');
      username = prefs.getString('username');
    }
  }

  Future<void> logout() async {
    _token = null;
    userId = null;
    username = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user_id');
    await prefs.remove('username');
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/login'),
          headers: _headers,
          body: jsonEncode({'username': username, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && data['access_token'] != null) {
      _decodeToken(data['access_token']);
      await _persistSession();
    } else {
      throw Exception(data['detail']?.toString() ?? 'Login failed');
    }
    return data;
  }

  Future<Map<String, dynamic>> register(
      String username, String email, String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/register'),
          headers: _headers,
          body: jsonEncode({'username': username, 'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception(data['detail']?.toString() ?? 'Registration failed');
    }
    return data;
  }

  // ── Portfolio ─────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getPortfolio() async {
    final response = await http
        .get(Uri.parse('$baseUrl/etoro/portfolio'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getInstruments() async {
    final response = await http
        .get(Uri.parse('$baseUrl/etoro/instruments'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as List<dynamic>;
  }

  // ── Market Data ───────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getQuote(String symbol) async {
    final response = await http
        .get(Uri.parse('$baseUrl/market/quote/$symbol'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getStockHistory(String symbol) async {
    final response = await http
        .get(Uri.parse('$baseUrl/market/history/$symbol'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as List<dynamic>;
  }

  // ── Anomaly Detection ─────────────────────────────────────────────────────
  Future<Map<String, dynamic>> analyzePortfolio(
      List<Map<String, dynamic>> positions) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/anomaly/analyze'),
          headers: _headers,
          body: jsonEncode({'positions': positions}),
        )
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ── AI Agent ─────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> chatWithTori(int userId, String message) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/agent/chat'),
          headers: _headers,
          body: jsonEncode({'user_id': userId, 'message': message}),
        )
        .timeout(const Duration(seconds: 30));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> fetchHistory(int userId) async {
    final response = await http
        .get(Uri.parse('$baseUrl/agent/history/$userId'), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as List<dynamic>;
  }

  // ── Health ────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getHealth() async {
    final response = await http
        .get(Uri.parse('$baseUrl/health'), headers: _headers)
        .timeout(const Duration(seconds: 5));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ── Bank (BT PSD2) ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> connectBank() async {
    final response = await http
        .post(Uri.parse('$baseUrl/bank/connect'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> sandboxAuthorize() async {
    final response = await http
        .post(Uri.parse('$baseUrl/bank/sandbox-authorize'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> disconnectBank() async {
    await http
        .post(Uri.parse('$baseUrl/bank/disconnect'), headers: _headers)
        .timeout(const Duration(seconds: 10));
  }

  Future<Map<String, dynamic>> sandboxAutoConnect() async {
    final response = await http
        .post(Uri.parse('$baseUrl/bank/sandbox-auto-connect'), headers: _headers)
        .timeout(const Duration(seconds: 30));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('${response.statusCode}: ${response.body}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getBankAccounts() async {
    final response = await http
        .get(Uri.parse('$baseUrl/bank/accounts'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getBankBalances(String accountId) async {
    final response = await http
        .get(Uri.parse('$baseUrl/bank/balances/$accountId'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getBankTransactions({String? monthYear, int limit = 100}) async {
    var url = '$baseUrl/bank/transactions?limit=$limit';
    if (monthYear != null) url += '&month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 20));
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> syncBank() async {
    final response = await http
        .post(Uri.parse('$baseUrl/bank/sync'), headers: _headers)
        .timeout(const Duration(seconds: 30));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getSubscriptions() async {
    final response = await http
        .get(Uri.parse('$baseUrl/bank/subscriptions'), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getSpendingSummary({String? monthYear}) async {
    var url = '$baseUrl/bank/spending-summary';
    if (monthYear != null) url += '?month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ── Budget Manager ────────────────────────────────────────────────────────
  Future<List<dynamic>> getBudgets({String? monthYear}) async {
    var url = '$baseUrl/budget/';
    if (monthYear != null) url += '?month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createBudget(
      String category, String monthYear, double limit) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/budget/'),
          headers: _headers,
          body: jsonEncode({
            'category': category,
            'month_year': monthYear,
            'limit_amount': limit,
            'currency': 'RON',
          }),
        )
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> deleteBudget(int budgetId) async {
    await http
        .delete(Uri.parse('$baseUrl/budget/$budgetId'), headers: _headers)
        .timeout(const Duration(seconds: 10));
  }

  Future<Map<String, dynamic>> getBudgetStatus({String? monthYear}) async {
    var url = '$baseUrl/budget/status';
    if (monthYear != null) url += '?month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ── Expense Analytics ─────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getExpenseInsights({String? monthYear}) async {
    var url = '$baseUrl/expenses/insights';
    if (monthYear != null) url += '?month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 30));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getExpenseCategories({String? monthYear}) async {
    var url = '$baseUrl/expenses/categories';
    if (monthYear != null) url += '?month_year=$monthYear';
    final response = await http
        .get(Uri.parse(url), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}

// Singleton instance
final apiService = ApiService();
