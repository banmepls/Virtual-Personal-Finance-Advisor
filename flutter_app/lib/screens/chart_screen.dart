import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/portfolio_model.dart';
import '../services/api_service.dart';

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
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadingQuote = false;
        _loadingHistory = false;
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
                  color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
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
                      color: selected ? const Color(0xFF1F6FEB) : const Color(0xFF21262D),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                          color: selected ? const Color(0xFF58A6FF) : const Color(0xFF30363D)),
                    ),
                    child: Text(
                      pos.symbol,
                      style: GoogleFonts.inter(
                        color: selected ? Colors.white : const Color(0xFF8B949E),
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
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF30363D)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_selectedSymbol ?? '',
                          style: GoogleFonts.inter(
                              color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
                      Text(_quote!['source'] == 'mock' ? '📦 Mock Data' : '🔴 Live',
                          style: GoogleFonts.inter(
                              color: const Color(0xFF8B949E), fontSize: 11)),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '\$${(_quote!['price'] as num).toStringAsFixed(2)}',
                        style: GoogleFonts.inter(
                            color: Colors.white, fontSize: 22, fontWeight: FontWeight.w700),
                      ),
                      Text(
                        _quote!['change_percent'] ?? '0%',
                        style: GoogleFonts.inter(
                          color: (_quote!['change_percent'] ?? '').toString().contains('-')
                              ? const Color(0xFFF85149)
                              : const Color(0xFF3FB950),
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
            const Center(
              child: Text('Price data unavailable', style: TextStyle(color: Colors.grey)),
            ),
            const SizedBox(height: 16),
          ],
          // Price chart
          Expanded(
            child: (_loadingQuote || _loadingHistory)
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
                : Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF161B22),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF30363D)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('30-Day Historical Trend',
                            style: GoogleFonts.inter(
                                color: const Color(0xFF8B949E), fontSize: 12)),
                        const SizedBox(height: 12),
                        Expanded(
                          child: LineChart(
                            LineChartData(
                              gridData: FlGridData(
                                show: true,
                                getDrawingHorizontalLine: (v) => FlLine(
                                  color: const Color(0xFF30363D),
                                  strokeWidth: 1,
                                ),
                                getDrawingVerticalLine: (v) => FlLine(
                                  color: const Color(0xFF30363D),
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
                                          color: const Color(0xFF8B949E), fontSize: 9),
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
                                  color: const Color(0xFF58A6FF),
                                  barWidth: 2,
                                  dotData: const FlDotData(show: false),
                                  belowBarData: BarAreaData(
                                    show: true,
                                    color: const Color(0xFF1F6FEB).withOpacity(0.15),
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
