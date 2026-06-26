// lib/theme/app_colors.dart
// Single source of truth for the app's GitHub-style light palette.
// Screens reference these instead of redeclaring hex values locally.

import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const bg = Color(0xFFF6F8FA);       // scaffold background
  static const surface = Color(0xFFFFFFFF);  // cards, app bars
  static const border = Color(0xFFD0D7DE);   // hairline borders
  static const primary = Color(0xFF0969DA);  // accent blue (darker for light bg)
  static const muted = Color(0xFF656D76);    // secondary text

  static const textPrimary = Color(0xFF1F2328);   // primary text on light
  static const textSecondary = Color(0xFF656D76); // secondary text on light

  static const green = Color(0xFF1A7F37);    // positive / income
  static const red = Color(0xFFCF222E);      // negative / debit / error
  static const gold = Color(0xFF9A6700);     // warning / amber
  static const purple = Color(0xFF8250DF);   // subscriptions

  // Shared categorical palette for charts / treemaps.
  static const chart = <Color>[
    Color(0xFF0969DA),
    Color(0xFF1A7F37),
    Color(0xFF9A6700),
    Color(0xFF8250DF),
    Color(0xFFBF5700),
    Color(0xFFCF222E),
    Color(0xFF0E8A84),
    Color(0xFF2DA44E),
  ];
}
