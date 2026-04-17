import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../models/bank_model.dart';
import '../services/api_service.dart';

class BankScreen extends StatefulWidget {
  const BankScreen({super.key});

  @override
  State<BankScreen> createState() => _BankScreenState();
}

class _BankScreenState extends State<BankScreen> {
  List<BankTransaction> _transactions = [];
  BankBalance? _balance;
  BankAccount? _account;
  bool _loading = true;
  bool _syncing = false;
  String? _error;
  String _selectedMonth = DateFormat('yyyy-MM').format(DateTime.now());

  static const _primary = Color(0xFF58A6FF);
  static const _surface = Color(0xFF161B22);
  static const _bg = Color(0xFF0D1117);
  static const _border = Color(0xFF30363D);
  static const _muted = Color(0xFF8B949E);
  static const _green = Color(0xFF3FB950);
  static const _red = Color(0xFFF85149);
  static const _gold = Color(0xFFD29922);

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      // Auto-connect (sandbox) + load accounts
      await apiService.connectBank();
      final accounts = await apiService.getBankAccounts();
      if (accounts.isNotEmpty) {
        _account = BankAccount.fromJson(accounts.first as Map<String, dynamic>);
        final balanceData = await apiService.getBankBalances(_account!.resourceId);
        _balance = BankBalance.fromJson(balanceData);
      }
      final txData = await apiService.getBankTransactions(monthYear: _selectedMonth, limit: 100);
      setState(() {
        _transactions = txData
            .map((t) => BankTransaction.fromJson(t as Map<String, dynamic>))
            .toList();
        _loading = false;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _sync() async {
    setState(() => _syncing = true);
    try {
      final result = await apiService.syncBank();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ ${result['message'] ?? 'Synced!'}',
              style: GoogleFonts.inter()),
          backgroundColor: const Color(0xFF238636),
        ),
      );
      await _loadData();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sync failed: $e'), backgroundColor: _red),
      );
    } finally {
      setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _primary))
          : _error != null
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadData,
                  color: _primary,
                  child: CustomScrollView(
                    slivers: [
                      _buildAppBar(),
                      SliverToBoxAdapter(child: _buildAccountCard()),
                      SliverToBoxAdapter(child: _buildMonthSelector()),
                      SliverToBoxAdapter(
                        child: Padding(
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                          child: Text(
                            'Transactions · ${_transactions.length}',
                            style: GoogleFonts.inter(color: _muted, fontSize: 13),
                          ),
                        ),
                      ),
                      SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (ctx, i) => _buildTransactionTile(_transactions[i]),
                          childCount: _transactions.length,
                        ),
                      ),
                      const SliverToBoxAdapter(child: SizedBox(height: 24)),
                    ],
                  ),
                ),
    );
  }

  Widget _buildAppBar() {
    return SliverAppBar(
      backgroundColor: _surface,
      pinned: true,
      elevation: 0,
      title: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: const Color(0xFF1F3A8A).withOpacity(0.4),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.account_balance, color: _primary, size: 18),
          ),
          const SizedBox(width: 10),
          Text('Banca Transilvania',
              style: GoogleFonts.inter(
                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 17)),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFF238636).withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF238636).withOpacity(0.6)),
            ),
            child: Text('SANDBOX',
                style: GoogleFonts.inter(
                    color: _green, fontSize: 9, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
      actions: [
        _syncing
            ? const Padding(
                padding: EdgeInsets.all(16),
                child: SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: _primary)))
            : IconButton(
                icon: const Icon(Icons.sync, color: _primary),
                onPressed: _sync,
                tooltip: 'Sync from BT',
              ),
      ],
    );
  }

  Widget _buildAccountCard() {
    final balance = _balance?.closingBooked ?? 0.0;
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1A3A6B), Color(0xFF0D1A3A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1F6FEB).withOpacity(0.5)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1F6FEB).withOpacity(0.15),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Available Balance',
                  style: GoogleFonts.inter(color: Colors.white70, fontSize: 13)),
              const Icon(Icons.credit_card, color: Colors.white54, size: 22),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            NumberFormat.currency(locale: 'ro_RO', symbol: 'RON ', decimalDigits: 2)
                .format(balance),
            style: GoogleFonts.inter(
                color: Colors.white, fontSize: 30, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          Text(_account?.maskedIban ?? 'RO** **** **** ****',
              style: GoogleFonts.robotoMono(color: Colors.white60, fontSize: 13)),
          const SizedBox(height: 4),
          Text(_account?.name ?? 'Cont Curent',
              style: GoogleFonts.inter(color: Colors.white54, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildMonthSelector() {
    final months = _generateMonths();
    return SizedBox(
      height: 48,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: months.length,
        itemBuilder: (ctx, i) {
          final m = months[i];
          final selected = m == _selectedMonth;
          return GestureDetector(
            onTap: () {
              setState(() => _selectedMonth = m);
              _loadData();
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: selected ? _primary : _surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                    color: selected ? _primary : _border, width: selected ? 0 : 1),
              ),
              alignment: Alignment.center,
              child: Text(
                DateFormat('MMM yyyy').format(DateTime.parse('$m-01')),
                style: GoogleFonts.inter(
                    color: selected ? Colors.white : _muted,
                    fontSize: 12,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w400),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTransactionTile(BankTransaction tx) {
    final isDebit = tx.isDebit;
    final color = isDebit ? _red : _green;
    final amountStr =
        '${isDebit ? '-' : '+'}${tx.amount.abs().toStringAsFixed(2)} ${tx.currency}';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: _categoryColor(tx.category).withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(_categoryIcon(tx.category),
                color: _categoryColor(tx.category), size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tx.merchantName,
                  style: GoogleFonts.inter(
                      color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: _categoryColor(tx.category).withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(tx.category,
                          style: GoogleFonts.inter(
                              color: _categoryColor(tx.category),
                              fontSize: 10,
                              fontWeight: FontWeight.w600)),
                    ),
                    if (tx.isRecurring) ...[
                      const SizedBox(width: 6),
                      const Icon(Icons.repeat, color: _gold, size: 12),
                    ],
                    const SizedBox(width: 6),
                    Text(tx.bookingDate ?? '',
                        style: GoogleFonts.inter(color: _muted, fontSize: 11)),
                  ],
                ),
              ],
            ),
          ),
          Text(
            amountStr,
            style: GoogleFonts.inter(
                color: color, fontSize: 13, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.wifi_off, color: _muted, size: 48),
          const SizedBox(height: 12),
          Text('Could not load bank data',
              style: GoogleFonts.inter(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 8),
          Text(_error ?? '',
              style: GoogleFonts.inter(color: _muted, fontSize: 12),
              textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadData,
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF238636)),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  List<String> _generateMonths() {
    final now = DateTime.now();
    return List.generate(6, (i) {
      final d = DateTime(now.year, now.month - i, 1);
      return DateFormat('yyyy-MM').format(d);
    });
  }

  Color _categoryColor(String cat) {
    const map = {
      'Food & Groceries': Color(0xFF3FB950),
      'Transport': Color(0xFFF0883E),
      'Utilities': Color(0xFF58A6FF),
      'Dining': Color(0xFFBC8CFF),
      'Shopping': Color(0xFFD29922),
      'Health': Color(0xFFFF4C8B),
      'Entertainment': Color(0xFF79C0FF),
      'Subscriptions': Color(0xFFD2A8FF),
      'Rent': Color(0xFFF85149),
      'Income': Color(0xFF3FB950),
      'Other': Color(0xFF8B949E),
    };
    return map[cat] ?? const Color(0xFF8B949E);
  }

  IconData _categoryIcon(String cat) {
    const map = {
      'Food & Groceries': Icons.shopping_cart,
      'Transport': Icons.directions_car,
      'Utilities': Icons.bolt,
      'Dining': Icons.restaurant,
      'Shopping': Icons.shopping_bag,
      'Health': Icons.local_hospital,
      'Entertainment': Icons.movie,
      'Subscriptions': Icons.subscriptions,
      'Rent': Icons.home,
      'Income': Icons.attach_money,
      'Other': Icons.receipt,
    };
    return map[cat] ?? Icons.receipt;
  }
}
