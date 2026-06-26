import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../widgets/treemap_chart.dart';
import '../models/portfolio_model.dart';
import '../models/bank_model.dart';
import '../services/api_service.dart';
import 'anomaly_screen.dart';
import 'chart_screen.dart';
import 'chat_screen.dart';
import 'bank_screen.dart';
import 'budget_screen.dart';
import 'subscription_screen.dart';
import 'expense_ai_screen.dart';
import 'auth_screen.dart';

class DashboardScreen extends StatefulWidget {
  final int initialIndex;
  const DashboardScreen({super.key, this.initialIndex = 2});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  Portfolio? _portfolio;
  double? _bankBalance;
  double? _monthSpend;
  bool _loading = true;
  String? _error;
  late int _selectedIndex;

  // Controllers for the nested hub TabBars, so quick-access can target a sub-tab.
  late final TabController _moneyTab = TabController(length: 3, vsync: this);
  late final TabController _analyticsTab = TabController(length: 2, vsync: this);

  /// Honest data-source indicator: the mock portfolio reports username 'demo_user'.
  bool get _isLive =>
      _portfolio != null && _portfolio!.username != 'demo_user' &&
      _portfolio!.username.isNotEmpty;

  @override
  void initState() {
    super.initState();
    _selectedIndex = widget.initialIndex;
    _loadHome();
  }

  @override
  void dispose() {
    _moneyTab.dispose();
    _analyticsTab.dispose();
    super.dispose();
  }

  Future<void> _loadHome() async {
    try {
      final data = await apiService.getPortfolio();
      Portfolio? p;
      if (data['error'] == null && data['positions'] != null) {
        p = Portfolio.fromJson(data);
      }

      // Bank balance (best-effort — Home stays usable if this fails).
      double? bal;
      try {
        final accounts = await apiService.getBankAccounts();
        if (accounts.isNotEmpty) {
          final acc = accounts.first as Map<String, dynamic>;
          final balData = await apiService.getBankBalances(acc['resource_id']);
          bal = BankBalance.fromJson(balData).closingBooked;
        }
      } catch (_) {/* ignore */}

      // This-month spending (best-effort).
      double? spend;
      try {
        final summary = await apiService.getSpendingSummary();
        spend = (summary['total_spent'] as num?)?.toDouble();
      } catch (_) {/* ignore */}

      setState(() {
        _portfolio = p;
        _bankBalance = bal;
        _monthSpend = spend;
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

  void _goToTab(int index, [int? sub]) {
    setState(() {
      _selectedIndex = index;
      if (index == 3 && sub != null) _moneyTab.index = sub;
      if (index == 4 && sub != null) _analyticsTab.index = sub;
    });
  }

  Future<void> _confirmLogout() async {
    Navigator.pop(context); // close the profile sheet
    await apiService.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const AuthScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    // ── 5 top-level screens ──────────────────────────────────────────────────
    // Tab 0: Portfolio (investment overview)
    // Tab 1: Bank (BT transactions)
    // Tab 2: Tori Chat (AI) ← CENTER
    // Tab 3: Money (Budget + Subscriptions + Expenses)
    // Tab 4: Analytics (Charts + Anomaly)

    final List<Widget> screens = [
      // ── Tab 0: Home (overview + investments) ──────────────────────────────
      _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
          : _error != null
              ? _buildError()
              : _buildHomeView(),

      // ── Tab 1: Bank ───────────────────────────────────────────────────────
      const BankScreen(),

      // ── Tab 2: Tori AI (CENTER) ───────────────────────────────────────────
      ChatScreen(userId: apiService.userId ?? 1),

      // ── Tab 3: Money (Budget + Subscriptions + Expenses) ──────────────────
      _buildMoneyHub(),

      // ── Tab 4: Analytics (Charts + Anomaly) ───────────────────────────────
      _buildAnalyticsHub(),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8FA),
      appBar: _selectedIndex == 0
          ? AppBar(
              backgroundColor: const Color(0xFFFFFFFF),
              elevation: 0,
              title: Text(
                'Virtual Finance Advisor',
                style: GoogleFonts.inter(
                  color: const Color(0xFF1F2328),
                  fontWeight: FontWeight.w700,
                  fontSize: 18,
                ),
              ),
              actions: [
                _buildSourceBadge(),
                IconButton(
                  icon: const Icon(Icons.account_circle_outlined,
                      color: Color(0xFF656D76)),
                  tooltip: 'Profile',
                  onPressed: _showProfileSheet,
                ),
                const SizedBox(width: 4),
              ],
            )
          : null,
      // IndexedStack keeps every tab alive → scroll position, chat history and
      // in-progress input survive switching tabs.
      body: IndexedStack(index: _selectedIndex, children: screens),
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFFFFFFFF),
        indicatorColor: const Color(0xFF0969DA).withOpacity(0.15),
        selectedIndex: _selectedIndex,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined, color: Color(0xFF656D76)),
            selectedIcon: const Icon(Icons.home, color: Color(0xFF0969DA)),
            label: 'Home',
          ),
          NavigationDestination(
            icon: const Icon(Icons.account_balance_outlined,
                color: Color(0xFF656D76)),
            selectedIcon: const Icon(Icons.account_balance,
                color: Color(0xFF0969DA)),
            label: 'Bank',
          ),
          // ── CENTER: Tori AI ──────────────────────────────────────────────
          NavigationDestination(
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0969DA), Color(0xFF218BFF)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.smart_toy, color: Colors.white, size: 22),
            ),
            selectedIcon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0969DA), Color(0xFF54AEFF)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Color(0xFF0969DA),
                    blurRadius: 12,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: const Icon(Icons.smart_toy, color: Colors.white, size: 22),
            ),
            label: 'Tori',
          ),
          NavigationDestination(
            icon: const Icon(Icons.savings_outlined,
                color: Color(0xFF656D76)),
            selectedIcon: const Icon(Icons.savings,
                color: Color(0xFF0969DA)),
            label: 'Money',
          ),
          NavigationDestination(
            icon: const Icon(Icons.analytics_outlined,
                color: Color(0xFF656D76)),
            selectedIcon: const Icon(Icons.analytics,
                color: Color(0xFF0969DA)),
            label: 'Analytics',
          ),
        ],
      ),
    );
  }

  // ── Tab 2: Money hub — Budget / Subscriptions / Expenses ──────────────────
  Widget _buildMoneyHub() {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFFFFFF),
        elevation: 0,
        title: Text('Money',
            style: GoogleFonts.inter(
                color: const Color(0xFF1F2328), fontWeight: FontWeight.w700, fontSize: 18)),
        bottom: TabBar(
          controller: _moneyTab,
          indicatorColor: const Color(0xFF0969DA),
          labelColor: const Color(0xFF0969DA),
          unselectedLabelColor: const Color(0xFF656D76),
          labelStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
          tabs: const [
            Tab(text: 'Budget', icon: Icon(Icons.pie_chart, size: 18)),
            Tab(text: 'Subscriptions', icon: Icon(Icons.repeat, size: 18)),
            Tab(text: 'AI Analysis', icon: Icon(Icons.auto_awesome, size: 18)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _moneyTab,
        children: const [
          BudgetScreen(),
          SubscriptionScreen(),
          ExpenseAIScreen(),
        ],
      ),
    );
  }

  // ── Tab 3: Analytics hub — Charts / Anomaly ───────────────────────────────
  Widget _buildAnalyticsHub() {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFFFFFF),
        elevation: 0,
        title: Text('Analytics',
            style: GoogleFonts.inter(
                color: const Color(0xFF1F2328), fontWeight: FontWeight.w700, fontSize: 18)),
        bottom: TabBar(
          controller: _analyticsTab,
          indicatorColor: const Color(0xFF0969DA),
          labelColor: const Color(0xFF0969DA),
          unselectedLabelColor: const Color(0xFF656D76),
          labelStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
          tabs: const [
            Tab(text: 'Charts', icon: Icon(Icons.candlestick_chart, size: 18)),
            Tab(text: 'Anomaly', icon: Icon(Icons.warning_amber, size: 18)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _analyticsTab,
        children: [
          ChartScreen(positions: _portfolio?.positions ?? []),
          AnomalyScreen(positions: _portfolio?.positions ?? []),
        ],
      ),
    );
  }

  // ── Home / Overview (Tab 0) ───────────────────────────────────────────────
  Widget _buildHomeView() {
    return RefreshIndicator(
      onRefresh: _loadHome,
      color: const Color(0xFF0969DA),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildOverviewCard(),
          const SizedBox(height: 16),
          _buildQuickAccess(),
          const SizedBox(height: 20),
          if (_portfolio != null && _portfolio!.positions.isNotEmpty) ...[
            Text('Investments',
                style: GoogleFonts.inter(
                    color: const Color(0xFF1F2328), fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            _buildMiniChart(),
            const SizedBox(height: 16),
            ..._portfolio!.positions.map(_buildPositionCard),
          ] else
            _buildInvestmentsUnavailable(),
        ],
      ),
    );
  }

  Widget _buildOverviewCard() {
    final hasInv = _portfolio != null;
    final invValue = _portfolio?.totalPortfolioValue ?? 0;
    final pnl = _portfolio?.totalPnL ?? 0;
    final pnlPct = _portfolio?.totalPnLPercent ?? 0;
    final isPos = pnl >= 0;
    final ron = NumberFormat.currency(locale: 'ro_RO', symbol: 'RON ', decimalDigits: 2);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF0969DA).withOpacity(0.15),
            const Color(0xFFFFFFFF),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD0D7DE)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Your Money',
              style: GoogleFonts.inter(color: const Color(0xFF656D76), fontSize: 13)),
          const SizedBox(height: 20),
          // ── Row 1: Investments ───────────────────────────────────────────
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: const Color(0xFF0969DA).withOpacity(0.10),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.show_chart, color: Color(0xFF0969DA), size: 20),
              ),
              const SizedBox(width: 12),
              Text('Investments',
                  style: GoogleFonts.inter(
                      color: const Color(0xFF1F2328), fontSize: 15, fontWeight: FontWeight.w600)),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    hasInv ? '\$${invValue.toStringAsFixed(2)}' : '—',
                    style: GoogleFonts.inter(
                        color: const Color(0xFF1F2328), fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                  if (hasInv)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(isPos ? Icons.trending_up : Icons.trending_down,
                            color: isPos ? const Color(0xFF1A7F37) : const Color(0xFFCF222E),
                            size: 14),
                        const SizedBox(width: 4),
                        Text(
                          '${isPos ? "+" : ""}${pnlPct.toStringAsFixed(2)}%',
                          style: GoogleFonts.inter(
                              color: isPos ? const Color(0xFF1A7F37) : const Color(0xFFCF222E),
                              fontSize: 12,
                              fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Divider(color: Color(0xFFD0D7DE), height: 1),
          ),
          // ── Row 2: Bank ──────────────────────────────────────────────────
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: const Color(0xFF1A7F37).withOpacity(0.10),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.account_balance, color: Color(0xFF1A7F37), size: 19),
              ),
              const SizedBox(width: 12),
              Text('Bank',
                  style: GoogleFonts.inter(
                      color: const Color(0xFF1F2328), fontSize: 15, fontWeight: FontWeight.w600)),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    _bankBalance != null ? ron.format(_bankBalance) : '—',
                    style: GoogleFonts.inter(
                        color: const Color(0xFF1F2328), fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                  if (_monthSpend != null)
                    Text('${_monthSpend!.toStringAsFixed(0)} RON spent this month',
                        style: GoogleFonts.inter(
                            color: const Color(0xFF656D76), fontSize: 11)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAccess() {
    // (icon, label, color, tab, subTab)
    final items = [
      (Icons.account_balance, 'Bank', const Color(0xFF1A7F37), 1, 0),
      (Icons.savings, 'Budget', const Color(0xFF9A6700), 3, 0),
      (Icons.repeat, 'Subs', const Color(0xFF8250DF), 3, 1),
      (Icons.auto_awesome, 'Expenses', const Color(0xFFBF5700), 3, 2),
      (Icons.analytics, 'Analytics', const Color(0xFF0969DA), 4, 0),
      (Icons.smart_toy, 'Tori', const Color(0xFF0969DA), 2, 0),
    ];
    return SizedBox(
      height: 78,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (ctx, i) {
          final (icon, label, color, tab, sub) = items[i];
          return GestureDetector(
            onTap: () => _goToTab(tab, sub),
            child: Container(
              width: 78,
              decoration: BoxDecoration(
                color: const Color(0xFFFFFFFF),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFD0D7DE)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                        color: color.withOpacity(0.14), shape: BoxShape.circle),
                    child: Icon(icon, color: color, size: 19),
                  ),
                  const SizedBox(height: 6),
                  Text(label,
                      style: GoogleFonts.inter(
                          color: const Color(0xFF1F2328), fontSize: 12, fontWeight: FontWeight.w500)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInvestmentsUnavailable() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFFFF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFD0D7DE)),
      ),
      child: Row(
        children: [
          const Icon(Icons.show_chart, color: Color(0xFF656D76), size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Investment data is currently unavailable. Pull down to refresh.',
              style: GoogleFonts.inter(color: const Color(0xFF656D76), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  // ── Data-source badge + profile sheet ─────────────────────────────────────
  Widget _buildSourceBadge() {
    final live = _isLive;
    final color = live ? const Color(0xFF1A7F37) : const Color(0xFF9A6700);
    return Container(
      margin: const EdgeInsets.only(right: 4),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.18),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(live ? Icons.wifi_tethering : Icons.science_outlined,
              color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            live ? 'LIVE' : 'DEMO',
            style: GoogleFonts.inter(
                color: color, fontSize: 11, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  void _showProfileSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFFFFFFFF),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(
                        color: Color(0xFFE8ECF1), shape: BoxShape.circle),
                    child: const Icon(Icons.person, color: Color(0xFF0969DA)),
                  ),
                  const SizedBox(width: 14),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(apiService.username ?? 'Guest',
                          style: GoogleFonts.inter(
                              color: const Color(0xFF1F2328),
                              fontSize: 16,
                              fontWeight: FontWeight.w700)),
                      Text(
                          _isLive ? 'Live data connected' : 'Demo data mode',
                          style: GoogleFonts.inter(
                              color: const Color(0xFF656D76), fontSize: 12)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 20),
              const Divider(color: Color(0xFFD0D7DE), height: 1),
              const SizedBox(height: 8),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.logout, color: Color(0xFFCF222E)),
                title: Text('Log out',
                    style: GoogleFonts.inter(
                        color: const Color(0xFFCF222E),
                        fontSize: 15,
                        fontWeight: FontWeight.w600)),
                onTap: _confirmLogout,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMiniChart() {
    final positions = _portfolio!.positions;
    if (positions.isEmpty) return const SizedBox();

    const colors = [
      Color(0xFF0969DA),
      Color(0xFF1A7F37),
      Color(0xFF9A6700),
      Color(0xFF8250DF),
      Color(0xFFBF5700),
      Color(0xFFCF222E),
      Color(0xFF0E8A84),
      Color(0xFF2DA44E),
    ];

    final tiles = positions.asMap().entries.map((e) {
      final pos = e.value;
      return TreemapTile(
        label: pos.symbol,
        value: pos.currentValue.abs(),
        color: colors[e.key % colors.length],
        sublabel: '\$${pos.currentValue.abs().toStringAsFixed(0)}',
      );
    }).toList();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFFFF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFD0D7DE)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Allocation',
              style: GoogleFonts.inter(
                  color: const Color(0xFF656D76), fontSize: 12)),
          const SizedBox(height: 10),
          TreemapChart(tiles: tiles, height: 220),
        ],
      ),
    );
  }

  Widget _buildPositionCard(PortfolioPosition pos) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFFFF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFD0D7DE)),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xFFE8ECF1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                pos.symbol.substring(0, pos.symbol.length > 2 ? 2 : pos.symbol.length),
                style: GoogleFonts.inter(
                    color: const Color(0xFF0969DA),
                    fontSize: 13,
                    fontWeight: FontWeight.w700),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(pos.name,
                    style: GoogleFonts.inter(
                        color: const Color(0xFF1F2328),
                        fontSize: 14,
                        fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                Text('${pos.quantity.toStringAsFixed(2)} @ \$${pos.avgBuyPrice.toStringAsFixed(2)}',
                    style: GoogleFonts.inter(
                        color: const Color(0xFF656D76), fontSize: 12)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${pos.currentValue.toStringAsFixed(2)}',
                style: GoogleFonts.inter(
                    color: const Color(0xFF1F2328),
                    fontSize: 14,
                    fontWeight: FontWeight.w600),
              ),
              Text(
                '${pos.isProfit ? "+" : ""}\$${pos.unrealizedPnl.toStringAsFixed(2)}',
                style: GoogleFonts.inter(
                  color: pos.isProfit
                      ? const Color(0xFF1A7F37)
                      : const Color(0xFFCF222E),
                  fontSize: 12,
                ),
              ),
            ],
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
          const Icon(Icons.wifi_off, color: Color(0xFF656D76), size: 48),
          const SizedBox(height: 12),
          Text('Backend unavailable',
              style: GoogleFonts.inter(color: const Color(0xFF1F2328), fontSize: 16)),
          const SizedBox(height: 8),
          Text(_error ?? '',
              style: GoogleFonts.inter(
                   color: const Color(0xFF656D76), fontSize: 12),
              textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              setState(() => _loading = true);
              _loadHome();
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1A7F37)),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
