// lib/theme/app_colors.dart
// Single source of truth for the app's GitHub-style dark palette.
// Screens reference these instead of redeclaring hex values locally.

import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const bg = Color(0xFF0D1117);       // scaffold background
  static const surface = Color(0xFF161B22);  // cards, app bars
  static const border = Color(0xFF30363D);   // hairline borders
  static const primary = Color(0xFF58A6FF);  // accent blue
  static const muted = Color(0xFF8B949E);    // secondary text

  static const green = Color(0xFF3FB950);    // positive / income
  static const red = Color(0xFFF85149);      // negative / debit / error
  static const gold = Color(0xFFD29922);     // warning / amber
  static const purple = Color(0xFFBC8CFF);   // subscriptions

  // Shared categorical palette for charts / treemaps.
  static const chart = <Color>[
    Color(0xFF58A6FF),
    Color(0xFF3FB950),
    Color(0xFFD29922),
    Color(0xFFBC8CFF),
    Color(0xFFF0883E),
    Color(0xFFFF4C8B),
    Color(0xFF39C5CF),
    Color(0xFF8DDB8C),
  ];
}
