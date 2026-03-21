import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/dashboard_screen.dart';

void main() {
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
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF58A6FF),
          surface: const Color(0xFF0D1117),
          surfaceContainerHighest: const Color(0xFF161B22),
        ),
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}
