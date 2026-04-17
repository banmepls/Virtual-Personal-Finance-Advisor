// lib/models/bank_model.dart
// Dart models for BT bank account, balance, and transaction data.

class BankAccount {
  final String resourceId;
  final String iban;
  final String currency;
  final String name;
  final String status;

  BankAccount({
    required this.resourceId,
    required this.iban,
    required this.currency,
    required this.name,
    required this.status,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) => BankAccount(
        resourceId: json['resource_id'] ?? '',
        iban: json['iban'] ?? '',
        currency: json['currency'] ?? 'RON',
        name: json['name'] ?? '',
        status: json['status'] ?? 'enabled',
      );

  String get maskedIban {
    if (iban.length <= 8) return iban;
    return '${iban.substring(0, 4)} **** **** ${iban.substring(iban.length - 4)}';
  }
}

class BankBalance {
  final String accountId;
  final String iban;
  final List<BalanceItem> balances;

  BankBalance({required this.accountId, required this.iban, required this.balances});

  factory BankBalance.fromJson(Map<String, dynamic> json) => BankBalance(
        accountId: json['account_id'] ?? '',
        iban: json['iban'] ?? '',
        balances: (json['balances'] as List? ?? [])
            .map((b) => BalanceItem.fromJson(b))
            .toList(),
      );

  double get closingBooked {
    final cb = balances.firstWhere(
      (b) => b.balanceType == 'closingBooked',
      orElse: () => balances.isNotEmpty ? balances.first : BalanceItem(balanceType: '', amount: 0, currency: 'RON'),
    );
    return cb.amount;
  }
}

class BalanceItem {
  final String balanceType;
  final double amount;
  final String currency;

  BalanceItem({required this.balanceType, required this.amount, required this.currency});

  factory BalanceItem.fromJson(Map<String, dynamic> json) {
    final ba = json['balance_amount'] ?? {};
    return BalanceItem(
      balanceType: json['balance_type'] ?? '',
      amount: double.tryParse(ba['amount']?.toString() ?? '0') ?? 0,
      currency: ba['currency'] ?? 'RON',
    );
  }
}

class BankTransaction {
  final int id;
  final String transactionId;
  final String? bookingDate;
  final double amount;
  final String currency;
  final String? creditorName;
  final String? debtorName;
  final String? remittanceInfo;
  final String category;
  final bool isRecurring;
  final bool isDebit;

  BankTransaction({
    required this.id,
    required this.transactionId,
    this.bookingDate,
    required this.amount,
    required this.currency,
    this.creditorName,
    this.debtorName,
    this.remittanceInfo,
    required this.category,
    required this.isRecurring,
    required this.isDebit,
  });

  factory BankTransaction.fromJson(Map<String, dynamic> json) => BankTransaction(
        id: json['id'] ?? 0,
        transactionId: json['transaction_id'] ?? '',
        bookingDate: json['booking_date'],
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
        currency: json['currency'] ?? 'RON',
        creditorName: json['creditor_name'],
        debtorName: json['debtor_name'],
        remittanceInfo: json['remittance_info'],
        category: json['category'] ?? 'Other',
        isRecurring: json['is_recurring'] ?? false,
        isDebit: json['is_debit'] ?? true,
      );

  String get merchantName => creditorName ?? debtorName ?? remittanceInfo ?? 'Unknown';
  bool get isExpense => isDebit && amount < 0;
}

class SpendingSummary {
  final String monthYear;
  final Map<String, double> categories;
  final double totalSpent;

  SpendingSummary({required this.monthYear, required this.categories, required this.totalSpent});

  factory SpendingSummary.fromJson(Map<String, dynamic> json) => SpendingSummary(
        monthYear: json['month_year'] ?? '',
        categories: Map<String, double>.from(
          (json['categories'] as Map? ?? {}).map((k, v) => MapEntry(k, (v as num).toDouble())),
        ),
        totalSpent: (json['total_spent'] as num?)?.toDouble() ?? 0,
      );
}

class Subscription {
  final String merchant;
  final double amount;
  final String currency;
  final String category;
  final String lastCharge;
  final String frequency;

  Subscription({
    required this.merchant,
    required this.amount,
    required this.currency,
    required this.category,
    required this.lastCharge,
    required this.frequency,
  });

  factory Subscription.fromJson(Map<String, dynamic> json) => Subscription(
        merchant: json['merchant'] ?? '',
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
        currency: json['currency'] ?? 'RON',
        category: json['category'] ?? '',
        lastCharge: json['last_charge'] ?? '',
        frequency: json['frequency'] ?? 'monthly',
      );
}
