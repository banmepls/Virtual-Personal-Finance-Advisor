import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use '10.0.2.2' for Android Emulator, '127.0.0.1' for iOS Simulator/Desktop
  // Use your machine's LAN IP (e.g., '192.168.1.x') for real devices.
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1'; 
  // static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
  String? _token;

  void setToken(String token) {
    _token = token;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  // ── Auth ──────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/login'),
          headers: _headers,
          body: jsonEncode({'username': username, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200) {
      _token = data['access_token'];
    }
    return data;
  }

  Future<Map<String, dynamic>> register(
      String username, String email, String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/register'),
          headers: _headers,
          body: jsonEncode(
              {'username': username, 'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));
    return jsonDecode(response.body) as Map<String, dynamic>;
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
}

// Singleton instance
final apiService = ApiService();
