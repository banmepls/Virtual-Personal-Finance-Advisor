import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/portfolio_model.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

class ChartScreen extends StatefulWidget {
  final List<PortfolioPosition> positions;
  const ChartScreen({super.key, required this.positions});

  @override
  State<ChartScreen> createState() => _ChartScreenState();
}

class _ChartScreenState extends State<ChartScreen> {
  String? _selectedSymbol;
  Map<String, dynamic>? _quote;
  List<dynamic> _history = [];
  bool _loadingQuote = false;
  bool _loadingHistory = false;
  String? _error;

  static const _primary = AppColors.primary;
  static const _bg = AppColors.bg;
  static const _surface = AppColors.surface;
  static const _border = AppColors.border;
  static const _muted = AppColors.muted;
  static const _textPrimary = AppColors.textPrimary;
  static const _chipBg = AppColors.chipBg;
  static const _green = AppColors.green;
  static const _red = AppColors.red;

  @override
  void initState() {
    super.initState();
    if (widget.positions.isNotEmpty) {
      _selectedSymbol = widget.positions.first.symbol;
      _fetchQuote(_selectedSymbol!);
    }
  }

  Future<void> _fetchQuote(String symbol) async {
    if (!mounted) return;
    setState(() {
      _loadingQuote = true;
      _loadingHistory = true;
      _error = null;
    });
    try {
      // 1. Fetch current quote
      final q = await apiService.getQuote(symbol);
      if (!mounted) return;

      // 2. Fetch 30-day history
      final h = await apiService.getStockHistory(symbol);

      if (!mounted) return;
      setState(() {
        _quote = q;
        _history = h;
        _loadingQuote = false;
        _loadingHistory = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadingQuote = false;
        _loadingHistory = false;
        _error = e.toString();
      });
    }
  }

  List<FlSpot> _getHistorySpots() {
    if (_history.isEmpty) return [const FlSpot(0, 0)];
    return _history.asMap().entries.map((e) {
      final val = e.value['price'];
      return FlSpot(e.key.toDouble(), (val is num) ? val.toDouble() : 0.0);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Market Charts',
              style: GoogleFonts.inter(
                  color: _textPrimary, fontSize: 20, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          // Symbol selector
          SizedBox(
            height: 40,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: widget.positions.length,
              itemBuilder: (ctx, i) {
                final pos = widget.positions[i];
                final selected = _selectedSymbol == pos.symbol;
                return GestureDetector(
                  onTap: () {
                    setState(() => _selectedSymbol = pos.symbol);
                    _fetchQuote(pos.symbol);
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: selected ? _primary : _chipBg,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                          color: selected ? _primary : _border),
                    ),
                    child: Text(
                      pos.symbol,
                      style: GoogleFonts.inter(
                        color: selected ? Colors.white : _muted,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 16),
          // Quote card
          if (_quote != null && _quote!['price'] != null) ...[
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: _surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _border),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_selectedSymbol ?? '',
                          style: GoogleFonts.inter(
                              color: _textPrimary, fontSize: 20, fontWeight: FontWeight.w700)),
                      Text(_quote!['source'] == 'mock' ? '📦 Mock Data' : '🔴 Live',
                          style: GoogleFonts.inter(
                              color: _muted, fontSize: 11)),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '\$${(_quote!['price'] as num).toStringAsFixed(2)}',
                        style: GoogleFonts.inter(
                            color: _textPrimary, fontSize: 22, fontWeight: FontWeight.w700),
                      ),
                      Text(
                        _quote!['change_percent'] ?? '0%',
                        style: GoogleFonts.inter(
                          color: (_quote!['change_percent'] ?? '').toString().contains('-')
                              ? _red
                              : _green,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ] else if (!_loadingQuote) ...[
            Center(
              child: Text('Price data unavailable', style: TextStyle(color: _muted)),
            ),
            const SizedBox(height: 16),
          ],
          // Price chart
          Expanded(
            child: (_loadingQuote || _loadingHistory)
                ? const Center(child: CircularProgressIndicator(color: _primary))
                : _error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.show_chart, color: AppColors.muted, size: 44),
                        const SizedBox(height: 12),
                        Text('Could not load chart data',
                            style: GoogleFonts.inter(color: _textPrimary, fontSize: 15)),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: _selectedSymbol == null
                              ? null
                              : () => _fetchQuote(_selectedSymbol!),
                          style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.green,
                              foregroundColor: Colors.white),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: _surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: _border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('30-Day Historical Trend',
                            style: GoogleFonts.inter(
                                color: _muted, fontSize: 12)),
                        const SizedBox(height: 12),
                        Expanded(
                          child: LineChart(
                            LineChartData(
                              gridData: FlGridData(
                                show: true,
                                getDrawingHorizontalLine: (v) => FlLine(
                                  color: _border,
                                  strokeWidth: 1,
                                ),
                                getDrawingVerticalLine: (v) => FlLine(
                                  color: _border,
                                  strokeWidth: 1,
                                ),
                              ),
                              titlesData: FlTitlesData(
                                topTitles: const AxisTitles(
                                    sideTitles: SideTitles(showTitles: false)),
                                rightTitles: const AxisTitles(
                                    sideTitles: SideTitles(showTitles: false)),
                                leftTitles: AxisTitles(
                                  sideTitles: SideTitles(
                                    showTitles: true,
                                    getTitlesWidget: (v, meta) => Text(
                                      '\$${v.toStringAsFixed(0)}',
                                      style: GoogleFonts.inter(
                                          color: _muted, fontSize: 9),
                                    ),
                                    reservedSize: 50,
                                  ),
                                ),
                                bottomTitles: const AxisTitles(
                                    sideTitles: SideTitles(showTitles: false)),
                              ),
                              borderData: FlBorderData(show: false),
                              lineBarsData: [
                                LineChartBarData(
                                  spots: _getHistorySpots(),
                                  isCurved: true,
                                  color: _primary,
                                  barWidth: 2,
                                  dotData: const FlDotData(show: false),
                                  belowBarData: BarAreaData(
                                    show: true,
                                    color: _primary.withOpacity(0.10),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
