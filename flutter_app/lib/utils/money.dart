// lib/utils/money.dart
// Shared currency formatting so RON/USD render consistently across screens.

import 'package:intl/intl.dart';

class Money {
  Money._();

  static final _ron = NumberFormat.currency(
      locale: 'ro_RO', symbol: 'RON ', decimalDigits: 2);

  /// "RON 1,234.56"
  static String ron(num value) => _ron.format(value);

  /// "1,235 RON" — compact, no decimals (for chips/summaries).
  static String ronCompact(num value) =>
      '${NumberFormat.decimalPattern('ro_RO').format(value.round())} RON';

  /// "$1,234.56"
  static String usd(num value) => '\$${value.toStringAsFixed(2)}';
}
