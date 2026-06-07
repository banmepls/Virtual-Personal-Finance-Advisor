import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await apiService.restoreSession();
  runApp(const FinanceAdvisorApp());
}

class FinanceAdvisorApp extends StatelessWidget {
  const FinanceAdvisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Virtual Finance Advisor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF58A6FF),
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        useMaterial3: true,
      ),
      // Skip the login screen if a session was restored from disk.
      home: apiService.isLoggedIn
          ? const DashboardScreen(initialIndex: 0)
          : const AuthScreen(),
    );
  }
}
