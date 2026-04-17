import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../models/budget_model.dart';
import '../services/api_service.dart';

class BudgetScreen extends StatefulWidget {
  const BudgetScreen({super.key});

  @override
  State<BudgetScreen> createState() => _BudgetScreenState();
}

class _BudgetScreenState extends State<BudgetScreen> {
  BudgetStatusResponse? _statusResponse;
  bool _loading = true;
  String? _error;
  String _selectedMonth = DateFormat('yyyy-MM').format(DateTime.now());

  static const _primary = Color(0xFF58A6FF);
  static const _surface = Color(0xFF161B22);
  static const _bg = Color(0xFF0D1117);
  static const _border = Color(0xFF30363D);
  static const _muted = Color(0xFF8B949E);
  static const _green = Color(0xFF3FB950);
  static const _red = Color(0xFFF85149);
  static const _amber = Color(0xFFD29922);

  static const _categories = [
    'Food & Groceries', 'Transport', 'Utilities', 'Dining',
    'Shopping', 'Health', 'Entertainment', 'Subscriptions', 'Rent', 'Other',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await apiService.getBudgetStatus(monthYear: _selectedMonth);
      setState(() {
        _statusResponse = BudgetStatusResponse.fromJson(data);
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

  void _showAddBudgetDialog() {
    String selectedCategory = _categories.first;
    final controller = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          backgroundColor: _surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text('Set Monthly Budget',
              style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w700)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selectedCategory,
                dropdownColor: _surface,
                decoration: InputDecoration(
                  labelText: 'Category',
                  labelStyle: GoogleFonts.inter(color: _muted),
                  enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _border)),
                  focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _primary)),
                ),
                style: GoogleFonts.inter(color: Colors.white),
                items: _categories.map((c) => DropdownMenuItem(
                  value: c, child: Text(c, style: GoogleFonts.inter(color: Colors.white)))).toList(),
                onChanged: (v) => setDialogState(() => selectedCategory = v!),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                style: GoogleFonts.inter(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Limit (RON)',
                  labelStyle: GoogleFonts.inter(color: _muted),
                  suffixText: 'RON',
                  suffixStyle: GoogleFonts.inter(color: _muted),
                  enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _border)),
                  focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: _primary)),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text('Cancel', style: GoogleFonts.inter(color: _muted)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: _primary),
              onPressed: () async {
                final limit = double.tryParse(controller.text);
                if (limit == null || limit <= 0) return;
                Navigator.pop(ctx);
                try {
                  await apiService.createBudget(selectedCategory, _selectedMonth, limit);
                  await _load();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: _red),
                  );
                }
              },
              child: Text('Save', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: _primary,
        onPressed: _showAddBudgetDialog,
        icon: const Icon(Icons.add, color: Colors.white),
        label: Text('Add Budget', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _primary))
          : _error != null
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _load,
                  color: _primary,
                  child: CustomScrollView(
                    slivers: [
                      SliverAppBar(
                        backgroundColor: _surface,
                        pinned: true,
                        elevation: 0,
                        title: Row(children: [
                          const Icon(Icons.pie_chart, color: _primary, size: 22),
                          const SizedBox(width: 10),
                          Text('Budget Manager',
                              style: GoogleFonts.inter(
                                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 17)),
                        ]),
                      ),
                      SliverToBoxAdapter(child: _buildMonthSelector()),
                      SliverToBoxAdapter(child: _buildSummaryRow()),
                      if (_statusResponse?.budgets.isEmpty ?? true)
                        SliverToBoxAdapter(child: _buildEmptyState())
                      else
                        SliverList(
                          delegate: SliverChildBuilderDelegate(
                            (ctx, i) => _buildBudgetCard(_statusResponse!.budgets[i]),
                            childCount: _statusResponse!.budgets.length,
                          ),
                        ),
                      const SliverToBoxAdapter(child: SizedBox(height: 80)),
                    ],
                  ),
                ),
    );
  }

  Widget _buildMonthSelector() {
    final now = DateTime.now();
    final months = List.generate(6, (i) =>
        DateFormat('yyyy-MM').format(DateTime(now.year, now.month - i, 1)));
    return SizedBox(
      height: 48,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: months.length,
        itemBuilder: (ctx, i) {
          final m = months[i];
          final sel = m == _selectedMonth;
          return GestureDetector(
            onTap: () { setState(() => _selectedMonth = m); _load(); },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: sel ? _primary : _surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: sel ? _primary : _border),
              ),
              alignment: Alignment.center,
              child: Text(DateFormat('MMM yyyy').format(DateTime.parse('$m-01')),
                  style: GoogleFonts.inter(
                      color: sel ? Colors.white : _muted,
                      fontSize: 12,
                      fontWeight: sel ? FontWeight.w700 : FontWeight.w400)),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummaryRow() {
    if (_statusResponse == null) return const SizedBox();
    final budgets = _statusResponse!.budgets;
    final exceeded = budgets.where((b) => b.status == 'exceeded').length;
    final warning = budgets.where((b) => b.status == 'warning').length;
    final ok = budgets.where((b) => b.status == 'ok').length;
    final totalSpent = budgets.fold(0.0, (s, b) => s + b.spentAmount);
    final totalLimit = budgets.fold(0.0, (s, b) => s + b.limitAmount);

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Expanded(child: _statChip('Spent', '${totalSpent.toStringAsFixed(0)} RON', _primary)),
          Expanded(child: _statChip('Budget', '${totalLimit.toStringAsFixed(0)} RON', _muted)),
          Expanded(child: _statChip('OK', '$ok', _green)),
          Expanded(child: _statChip('Alert', '$warning', _amber)),
          Expanded(child: _statChip('Over', '$exceeded', _red)),
        ],
      ),
    );
  }

  Widget _statChip(String label, String value, Color color) => Column(
    children: [
      Text(value, style: GoogleFonts.inter(color: color, fontSize: 15, fontWeight: FontWeight.w700)),
      const SizedBox(height: 2),
      Text(label, style: GoogleFonts.inter(color: _muted, fontSize: 11)),
    ],
  );

  Widget _buildBudgetCard(BudgetStatus b) {
    final pct = (b.percentageUsed / 100).clamp(0.0, 1.0);
    Color barColor;
    if (b.status == 'exceeded') {
      barColor = _red;
    } else if (b.status == 'warning') {
      barColor = _amber;
    } else {
      barColor = _green;
    }

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(_catIcon(b.category), color: _catColor(b.category), size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Text(b.category,
                    style: GoogleFonts.inter(
                        color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
              ),
              Text('${b.spentAmount.toStringAsFixed(0)} / ${b.limitAmount.toStringAsFixed(0)} RON',
                  style: GoogleFonts.inter(color: _muted, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: TweenAnimationBuilder<double>(
              tween: Tween(begin: 0, end: pct),
              duration: const Duration(milliseconds: 700),
              curve: Curves.easeOutCubic,
              builder: (_, v, __) => LinearProgressIndicator(
                value: v,
                minHeight: 8,
                backgroundColor: const Color(0xFF21262D),
                valueColor: AlwaysStoppedAnimation<Color>(barColor),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('${b.percentageUsed.toStringAsFixed(0)}% used',
                  style: GoogleFonts.inter(color: barColor, fontSize: 11, fontWeight: FontWeight.w600)),
              if (b.status == 'exceeded')
                Text('⚠️ Over by ${(b.spentAmount - b.limitAmount).toStringAsFixed(0)} RON',
                    style: GoogleFonts.inter(color: _red, fontSize: 11))
              else
                Text('${b.remaining.toStringAsFixed(0)} RON left',
                    style: GoogleFonts.inter(color: _muted, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Padding(
      padding: const EdgeInsets.all(40),
      child: Column(
        children: [
          const Icon(Icons.savings_outlined, color: _muted, size: 56),
          const SizedBox(height: 16),
          Text('No budgets yet',
              style: GoogleFonts.inter(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('Tap + Add Budget to set monthly spending limits per category.',
              style: GoogleFonts.inter(color: _muted, fontSize: 13),
              textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: _muted, size: 48),
          const SizedBox(height: 12),
          Text('Failed to load budgets',
              style: GoogleFonts.inter(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load,
              style: ElevatedButton.styleFrom(backgroundColor: _primary),
              child: const Text('Retry')),
        ],
      ),
    );
  }

  Color _catColor(String cat) {
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
      'Other': Color(0xFF8B949E),
    };
    return map[cat] ?? const Color(0xFF8B949E);
  }

  IconData _catIcon(String cat) {
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
      'Other': Icons.receipt,
    };
    return map[cat] ?? Icons.receipt;
  }
}
