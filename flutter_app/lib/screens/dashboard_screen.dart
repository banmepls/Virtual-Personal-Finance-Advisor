import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/portfolio_model.dart';
import '../models/anomaly_model.dart';
import '../services/api_service.dart';
import 'anomaly_screen.dart';
import 'chart_screen.dart';
import 'chat_screen.dart';

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
    final screens = [
      _buildPortfolioView(),
      ChartScreen(positions: _portfolio?.positions ?? []),
      AnomalyScreen(positions: _portfolio?.positions ?? []),
      ChatScreen(userId: 1), // Assuming user ID 1 for now
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
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
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
          : _error != null
              ? _buildError()
              : screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF161B22),
        indicatorColor: const Color(0xFF58A6FF).withOpacity(0.2),
        selectedIndex: _selectedIndex,
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
            icon: const Icon(Icons.candlestick_chart_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon: const Icon(Icons.candlestick_chart,
                color: Color(0xFF58A6FF)),
            label: 'Charts',
          ),
          NavigationDestination(
            icon: const Icon(Icons.warning_amber_outlined,
                color: Color(0xFF8B949E)),
            selectedIcon:
                const Icon(Icons.warning_amber, color: Color(0xFF58A6FF)),
            label: 'Anomaly',
          ),
          NavigationDestination(
            icon: const Icon(Icons.chat_bubble_outline,
                color: Color(0xFF8B949E)),
            selectedIcon:
                const Icon(Icons.chat_bubble, color: Color(0xFF58A6FF)),
            label: 'Tori',
          ),
        ],
      ),
    );
  }

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
                Text('${pos.quantity} × \$${pos.currentPrice.toStringAsFixed(2)}',
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
