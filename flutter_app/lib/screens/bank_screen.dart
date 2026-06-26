import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/bank_model.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../utils/money.dart';
import '../widgets/empty_state.dart';

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
  String? _authUrl;
  bool _usedRealApi = false;
  String _selectedMonth = DateFormat('yyyy-MM').format(DateTime.now());

  static const _primary = AppColors.primary;
  static const _surface = AppColors.surface;
  static const _bg = AppColors.bg;
  static const _border = AppColors.border;
  static const _muted = AppColors.muted;
  static const _green = AppColors.green;
  static const _red = AppColors.red;
  static const _gold = AppColors.gold;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      // Auto-connect (sandbox) + load accounts
      final connectRes = await apiService.connectBank();
      if (!mounted) return;
      final newAuthUrl = connectRes['auth_url']?.toString() ?? '';
      setState(() {
        _authUrl = newAuthUrl.isNotEmpty ? newAuthUrl : null;
        if (_authUrl == null) _usedRealApi = connectRes['is_sandbox'] == true;
      });

      if (_authUrl != null) {
        if (!mounted) return;
        setState(() {
          _loading = false;
          _account = null;
          _balance = null;
          _transactions = [];
        });
        return;
      }

      final accounts = await apiService.getBankAccounts();
      if (accounts.isNotEmpty) {
        final firstAccount = BankAccount.fromJson(accounts.first as Map<String, dynamic>);
        final balanceData = await apiService.getBankBalances(firstAccount.resourceId);
        if (mounted) {
          setState(() {
            _account = firstAccount;
            _balance = BankBalance.fromJson(balanceData);
          });
        }
      }
      final txData = await apiService.getBankTransactions(monthYear: _selectedMonth, limit: 100);
      if (!mounted) return;
      setState(() {
        _transactions = txData
            .map((t) => BankTransaction.fromJson(t as Map<String, dynamic>))
            .toList();
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  bool get _isRealAuthUrl => _authUrl != null && _authUrl!.startsWith('https://');

  Future<void> _launchAuthUrl() async {
    if (_authUrl == null) return;
    final uri = Uri.parse(_authUrl!);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open browser for authentication.')),
      );
    }
  }

  Future<void> _sandboxAutoConnect() async {
    setState(() => _loading = true);
    try {
      await apiService.sandboxAutoConnect();
      if (!mounted) return;
      setState(() => _authUrl = null);
      await _loadData();
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Auto-connect failed: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 5),
        ),
      );
    }
  }

  Future<void> _sandboxAuthorize() async {
    setState(() => _loading = true);
    try {
      await apiService.sandboxAuthorize();
      if (!mounted) return;
      setState(() => _authUrl = null);
      await _loadData();
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Authorization failed: $e'),
          backgroundColor: _red,
        ),
      );
    }
  }

  Future<bool> _confirmDisconnect() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: _surface,
        title: Text('Disconnect BT Account',
            style: TextStyle(color: AppColors.textPrimary)),
        content: Text(
          'This will clear the stored connection. You can reconnect via sandbox auto-connect or by logging in through the browser.',
          style: TextStyle(color: _muted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('Cancel', style: TextStyle(color: _muted)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Disconnect', style: TextStyle(color: AppColors.red)),
          ),
        ],
      ),
    );
    return confirmed ?? false;
  }

  Future<void> _disconnect() async {
    if (await _confirmDisconnect()) {
      setState(() => _loading = true);
      try {
        await apiService.disconnectBank();
        if (!mounted) return;
        await _loadData();
      } catch (e) {
        if (!mounted) return;
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Disconnect failed: $e'), backgroundColor: _red),
        );
      }
    }
  }

  Future<void> _sync() async {
    setState(() => _syncing = true);
    try {
      final result = await apiService.syncBank();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ ${result['message'] ?? 'Synced!'}',
              style: GoogleFonts.inter()),
          backgroundColor: const Color(0xFF238636),
        ),
      );
      await _loadData();
    } catch (e) {
      if (!mounted) return;
      setState(() => _syncing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sync failed: $e'), backgroundColor: _red),
      );
    } finally {
      if (mounted) setState(() => _syncing = false);
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
              : _authUrl != null && _account == null
                  ? _buildAuthRequired()
                  : _usedRealApi && _account == null
                      ? _buildSandboxConnected()
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
                      if (_transactions.isEmpty)
                        SliverToBoxAdapter(
                          child: EmptyState(
                            icon: Icons.receipt_long,
                            title: 'No transactions yet',
                            message:
                                'No transactions for this month. Tap sync to fetch the latest from your bank.',
                            actionLabel: 'Sync now',
                            onAction: _sync,
                          ),
                        )
                      else
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
          Expanded(
            child: Text('Banca Transilvania',
                style: GoogleFonts.inter(
                    color: AppColors.textPrimary, fontWeight: FontWeight.w700, fontSize: 17),
                overflow: TextOverflow.ellipsis),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFF238636).withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF238636).withOpacity(0.6)),
            ),
            child: Text(_usedRealApi ? 'SANDBOX' : 'DEMO DATA',
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
        IconButton(
          icon: const Icon(Icons.link_off, color: AppColors.muted),
          onPressed: _disconnect,
          tooltip: 'Disconnect / Reconnect',
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
            Money.ron(balance),
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
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                        decoration: BoxDecoration(
                          color: _categoryColor(tx.category).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          tx.category,
                          style: GoogleFonts.inter(
                              color: _categoryColor(tx.category),
                              fontSize: 11,
                              fontWeight: FontWeight.w600),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                    if (tx.isRecurring) ...[
                      const SizedBox(width: 6),
                      const Icon(Icons.repeat, color: _gold, size: 13),
                    ],
                    const SizedBox(width: 6),
                    Text(tx.bookingDate ?? '',
                        style: GoogleFonts.inter(color: _muted, fontSize: 12)),
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

  Widget _buildSandboxConnected() {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _surface,
        elevation: 0,
        title: Row(
          children: [
            const Icon(Icons.account_balance, color: _primary, size: 20),
            const SizedBox(width: 8),
            Text('Banca Transilvania',
                style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 17)),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
              decoration: BoxDecoration(
                color: _primary.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: _primary.withOpacity(0.6)),
              ),
              child: Text('BT SANDBOX',
                  style: GoogleFonts.inter(color: _primary, fontSize: 9, fontWeight: FontWeight.w700)),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.link_off, color: Color(0xFF8B949E)),
            onPressed: _disconnect,
            tooltip: 'Disconnect',
          ),
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: _primary.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.verified_user, color: _primary, size: 36),
              ),
              const SizedBox(height: 24),
              Text('BT Sandbox Connected',
                  style: GoogleFonts.inter(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Text(
                'Your bank connected successfully, but this test bank has no sample accounts to display.',
                style: GoogleFonts.inter(color: _muted, fontSize: 14, height: 1.6),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Tap below to load demo data and explore the app.',
                style: GoogleFonts.inter(color: _gold, fontSize: 13),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: _sandboxAuthorize,
                  icon: const Icon(Icons.account_balance, color: Colors.white),
                  label: Text('Connect Demo Data',
                      style: GoogleFonts.inter(
                          color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextButton.icon(
                onPressed: _disconnect,
                icon: const Icon(Icons.link_off, color: _muted, size: 16),
                label: Text('Disconnect', style: GoogleFonts.inter(color: _muted, fontSize: 13)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAuthRequired() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF1F3A8A).withOpacity(0.4),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.account_balance, color: _primary, size: 40),
            ),
            const SizedBox(height: 24),
            Text('Connect Your Bank',
                style: GoogleFonts.inter(
                    color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Text(
              'Connect a bank account to track your spending, budgets and subscriptions. '
              'Use demo data to explore everything instantly.',
              style: GoogleFonts.inter(color: _muted, fontSize: 14, height: 1.5),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            // ── Primary CTA: always the reliable demo path ──
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _sandboxAuthorize,
                icon: const Icon(Icons.account_balance, color: Colors.white),
                label: Text(
                  'Connect Demo Data',
                  style: GoogleFonts.inter(
                      color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _primary,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            // ── Advanced (developer) options, collapsed by default ──
            if (_isRealAuthUrl) ...[
              const SizedBox(height: 16),
              Theme(
                data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  iconColor: _muted,
                  collapsedIconColor: _muted,
                  title: Text('Advanced (developer) options',
                      style: GoogleFonts.inter(color: _muted, fontSize: 13)),
                  childrenPadding: const EdgeInsets.only(top: 4, bottom: 8),
                  children: [
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: OutlinedButton.icon(
                        onPressed: _launchAuthUrl,
                        icon: const Icon(Icons.open_in_browser, color: _primary, size: 18),
                        label: Text('Open BT Bank Login',
                            style: GoogleFonts.inter(
                                color: _primary, fontWeight: FontWeight.w600)),
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: _primary),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: OutlinedButton.icon(
                        onPressed: _sandboxAutoConnect,
                        icon: const Icon(Icons.flash_on, color: _muted, size: 18),
                        label: Text('Auto-connect (Sandbox OAuth2)',
                            style: GoogleFonts.inter(
                                color: _muted, fontWeight: FontWeight.w600)),
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: _border),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    TextButton.icon(
                      onPressed: _loadData,
                      icon: const Icon(Icons.refresh, color: _muted, size: 16),
                      label: Text('I have completed authentication',
                          style: GoogleFonts.inter(color: _muted, fontSize: 13)),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
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
