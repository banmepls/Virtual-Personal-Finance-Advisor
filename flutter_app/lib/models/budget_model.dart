// lib/models/budget_model.dart
// Dart models for budget management.

class Budget {
  final int id;
  final String category;
  final String monthYear;
  final double limitAmount;
  final String currency;

  Budget({
    required this.id,
    required this.category,
    required this.monthYear,
    required this.limitAmount,
    required this.currency,
  });

  factory Budget.fromJson(Map<String, dynamic> json) => Budget(
        id: json['id'] ?? 0,
        category: json['category'] ?? '',
        monthYear: json['month_year'] ?? '',
        limitAmount: (json['limit_amount'] as num?)?.toDouble() ?? 0,
        currency: json['currency'] ?? 'RON',
      );
}

class BudgetStatus {
  final String category;
  final double limitAmount;
  final double spentAmount;
  final double remaining;
  final double percentageUsed;
  final String currency;
  final String status; // "ok", "warning", "exceeded"

  BudgetStatus({
    required this.category,
    required this.limitAmount,
    required this.spentAmount,
    required this.remaining,
    required this.percentageUsed,
    required this.currency,
    required this.status,
  });

  factory BudgetStatus.fromJson(Map<String, dynamic> json) => BudgetStatus(
        category: json['category'] ?? '',
        limitAmount: (json['limit_amount'] as num?)?.toDouble() ?? 0,
        spentAmount: (json['spent_amount'] as num?)?.toDouble() ?? 0,
        remaining: (json['remaining'] as num?)?.toDouble() ?? 0,
        percentageUsed: (json['percentage_used'] as num?)?.toDouble() ?? 0,
        currency: json['currency'] ?? 'RON',
        status: json['status'] ?? 'ok',
      );
}

class BudgetStatusResponse {
  final String monthYear;
  final List<BudgetStatus> budgets;

  BudgetStatusResponse({required this.monthYear, required this.budgets});

  factory BudgetStatusResponse.fromJson(Map<String, dynamic> json) => BudgetStatusResponse(
        monthYear: json['month_year'] ?? '',
        budgets: (json['budgets'] as List? ?? [])
            .map((b) => BudgetStatus.fromJson(b))
            .toList(),
      );
}
