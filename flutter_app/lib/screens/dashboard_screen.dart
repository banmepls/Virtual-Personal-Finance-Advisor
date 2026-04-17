import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/portfolio_model.dart';
import '../models/anomaly_model.dart';
import '../services/api_service.dart';
import 'anomaly_screen.dart';
import 'chart_screen.dart';
import 'chat_screen.dart';
import 'bank_screen.dart';
import 'budget_screen.dart';
import 'subscription_screen.dart';
import 'expense_ai_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Portfolio? _portfolio;
  bool _loading = true;
  String? _error;
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadPortfolio();
  }

  Future<void> _loadPortfolio() async {
    try {
      final data = await apiService.getPortfolio();
      setState(() {
        _portfolio = Portfolio.fromJson(data);
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // ── 5 top-level screens ──────────────────────────────────────────────────
    // Tab 0: Portfolio (investment overview)
    // Tab 1: Bank (BT transactions)
    // Tab 2: Budget+Expenses (bank analytics)
    // Tab 3: Charts+Anomaly (portfolio analytics)
    // Tab 4: Tori Chat (AI)

    final List<Widget> screens = [
      // ── Tab 0: Portfolio ──────────────────────────────────────────────────
      _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
          : _error != null
              ? _buildError()
              : _buildPortfolioView(),

      // ── Tab 1: Bank ───────────────────────────────────────────────────────
      const BankScreen(),

      // ── Tab 2: Money (Budget + Subscriptions + Expenses) ──────────────────
      _buildMoneyHub(),

      // ── Tab 3: Analytics (Charts + Anomaly) ───────────────────────────────
      _buildAnalyticsHub(),

      // ── Tab 4: Tori AI ────────────────────────────────────────────────────
      ChatScreen(userId: 1),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: _selectedIndex == 0
          ? AppBar(
              backgroundColor: const Color(0xFF161B22),
              elevation: 0,
              title: Text(
                'Virtual Finance Advisor',
                style: GoogleFonts.inter(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 18,
                ),
              ),
              actions: [
                Container(
                  margin: const EdgeInsets.only(right: 12),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF238636),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'LIVE',
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            )
          : null,
      body: screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF161B22),
        indicatorColor: const Color(0xFF58A6FF).withOpacity(0.2),
        selectedIndex: _selectedIndex,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.account_balance_wallet_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.account_balance_wallet,
                color: Color(0xFF58A6FF)),
            label: 'Portfolio',
          ),
          NavigationDestination(
            icon: const Icon(Icons.account_balance_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.account_balance,
                color: Color(0xFF58A6FF)),
            label: 'Bank',
          ),
          NavigationDestination(
            icon: const Icon(Icons.savings_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.savings,
                color: Color(0xFF58A6FF)),
            label: 'Money',
          ),
          NavigationDestination(
            icon: const Icon(Icons.analytics_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.analytics,
                color: Color(0xFF58A6FF)),
            label: 'Analytics',
          ),
          NavigationDestination(
            icon: const Icon(Icons.smart_toy_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.smart_toy,
                color: Color(0xFF58A6FF)),
            label: 'Tori',
          ),
        ],
      ),
    );
  }

  // ── Tab 2: Money hub — Budget / Subscriptions / Expenses ──────────────────
  Widget _buildMoneyHub() {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: const Color(0xFF0D1117),
        appBar: AppBar(
          backgroundColor: const Color(0xFF161B22),
          elevation: 0,
          title: Text('Money',
              style: GoogleFonts.inter(
                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
          bottom: TabBar(
            indicatorColor: const Color(0xFF58A6FF),
            labelColor: const Color(0xFF58A6FF),
            unselectedLabelColor: const Color(0xFF8B949E),
            labelStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
            tabs: const [
              Tab(text: 'Budget', icon: Icon(Icons.pie_chart, size: 18)),
              Tab(text: 'Subscriptions', icon: Icon(Icons.repeat, size: 18)),
              Tab(text: 'AI Analysis', icon: Icon(Icons.auto_awesome, size: 18)),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            BudgetScreen(),
            SubscriptionScreen(),
            ExpenseAIScreen(),
          ],
        ),
      ),
    );
  }

  // ── Tab 3: Analytics hub — Charts / Anomaly ───────────────────────────────
  Widget _buildAnalyticsHub() {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: const Color(0xFF0D1117),
        appBar: AppBar(
          backgroundColor: const Color(0xFF161B22),
          elevation: 0,
          title: Text('Analytics',
              style: GoogleFonts.inter(
                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
          bottom: TabBar(
            indicatorColor: const Color(0xFF58A6FF),
            labelColor: const Color(0xFF58A6FF),
            unselectedLabelColor: const Color(0xFF8B949E),
            labelStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
            tabs: const [
              Tab(text: 'Charts', icon: Icon(Icons.candlestick_chart, size: 18)),
              Tab(text: 'Anomaly', icon: Icon(Icons.warning_amber, size: 18)),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            ChartScreen(positions: _portfolio?.positions ?? []),
            AnomalyScreen(positions: _portfolio?.positions ?? []),
          ],
        ),
      ),
    );
  }

  // ── Portfolio View (Tab 0) ────────────────────────────────────────────────
  Widget _buildPortfolioView() {
    if (_portfolio == null) return const SizedBox();
    return RefreshIndicator(
      onRefresh: _loadPortfolio,
      color: const Color(0xFF58A6FF),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSummaryCard(),
          const SizedBox(height: 16),
          _buildMiniChart(),
          const SizedBox(height: 16),
          Text(
            'Positions',
            style: GoogleFonts.inter(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          ..._portfolio!.positions.map(_buildPositionCard),
        ],
      ),
    );
  }

  Widget _buildSummaryCard() {
    final p = _portfolio!;
    final isPositive = p.totalPnL >= 0;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1F6FEB).withOpacity(0.3),
            const Color(0xFF161B22),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Total Portfolio Value',
              style: GoogleFonts.inter(
                  color: const Color(0xFF8B949E), fontSize: 13)),
          const SizedBox(height: 4),
          Text(
            '\$${p.totalPortfolioValue.toStringAsFixed(2)}',
            style: GoogleFonts.inter(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(
                isPositive ? Icons.trending_up : Icons.trending_down,
                color: isPositive
                    ? const Color(0xFF3FB950)
                    : const Color(0xFFF85149),
                size: 18,
              ),
              const SizedBox(width: 6),
              Text(
                '${isPositive ? "+" : ""}\$${p.totalPnL.toStringAsFixed(2)} (${p.totalPnLPercent.toStringAsFixed(2)}%)',
                style: GoogleFonts.inter(
                  color: isPositive
                      ? const Color(0xFF3FB950)
                      : const Color(0xFFF85149),
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMiniChart() {
    final positions = _portfolio!.positions;
    if (positions.isEmpty) return const SizedBox();
    return Container(
      height: 120,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: PieChart(
        PieChartData(
          sections: positions.asMap().entries.map((e) {
            final colors = [
              const Color(0xFF58A6FF),
              const Color(0xFF3FB950),
              const Color(0xFFD29922),
              const Color(0xFFBC8CFF),
              const Color(0xFFF0883E),
            ];
            return PieChartSectionData(
              value: e.value.currentValue.abs(),
              color: colors[e.key % colors.length],
              title: e.value.symbol,
              titleStyle: GoogleFonts.inter(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w600),
              radius: 50,
            );
          }).toList(),
          sectionsSpace: 2,
          centerSpaceRadius: 20,
        ),
      ),
    );
  }

  Widget _buildPositionCard(PortfolioPosition pos) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xFF21262D),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                pos.symbol.substring(0, pos.symbol.length > 2 ? 2 : pos.symbol.length),
                style: GoogleFonts.inter(
                    color: const Color(0xFF58A6FF),
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
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                Text('${pos.quantity.toStringAsFixed(2)} @ \$${pos.avgBuyPrice.toStringAsFixed(2)}',
                    style: GoogleFonts.inter(
                        color: const Color(0xFF8B949E), fontSize: 12)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${pos.currentValue.toStringAsFixed(2)}',
                style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600),
              ),
              Text(
                '${pos.isProfit ? "+" : ""}\$${pos.unrealizedPnl.toStringAsFixed(2)}',
                style: GoogleFonts.inter(
                  color: pos.isProfit
                      ? const Color(0xFF3FB950)
                      : const Color(0xFFF85149),
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
          const Icon(Icons.wifi_off, color: Color(0xFF8B949E), size: 48),
          const SizedBox(height: 12),
          Text('Backend unavailable',
              style: GoogleFonts.inter(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 8),
          Text(_error ?? '',
              style: GoogleFonts.inter(
                  color: const Color(0xFF8B949E), fontSize: 12),
              textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              setState(() => _loading = true);
              _loadPortfolio();
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF238636)),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
