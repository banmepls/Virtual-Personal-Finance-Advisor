import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';

class ExpenseAIScreen extends StatefulWidget {
  const ExpenseAIScreen({super.key});

  @override
  State<ExpenseAIScreen> createState() => _ExpenseAIScreenState();
}

class _ExpenseAIScreenState extends State<ExpenseAIScreen> {
  Map<String, double> _categories = {};
  String _aiSummary = '';
  double _totalSpent = 0;
  String _topCategory = '';
  bool _loading = true;
  bool _loadingInsight = false;
  String? _error;
  String _selectedMonth = DateFormat('yyyy-MM').format(DateTime.now());
  int _touchedIndex = -1;

  static const _primary = Color(0xFF58A6FF);
  static const _surface = Color(0xFF161B22);
  static const _bg = Color(0xFF0D1117);
  static const _border = Color(0xFF30363D);
  static const _muted = Color(0xFF8B949E);

  final _chartColors = const [
    Color(0xFF58A6FF),
    Color(0xFF3FB950),
    Color(0xFFD29922),
    Color(0xFFBC8CFF),
    Color(0xFFF0883E),
    Color(0xFFFF4C8B),
    Color(0xFF79C0FF),
    Color(0xFFF85149),
    Color(0xFFD2A8FF),
    Color(0xFF8B949E),
  ];

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    setState(() => _loading = true);
    try {
      final data = await apiService.getExpenseCategories(monthYear: _selectedMonth);
      final cats = Map<String, double>.from(
        (data['categories'] as Map? ?? {}).map((k, v) => MapEntry(k, (v as num).toDouble())),
      );
      setState(() {
        _categories = cats;
        _totalSpent = (data['total_spent'] as num?)?.toDouble() ?? cats.values.fold(0, (a, b) => a + b);
        _topCategory = cats.isNotEmpty
            ? cats.entries.reduce((a, b) => a.value > b.value ? a : b).key
            : 'N/A';
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

  Future<void> _loadInsight() async {
    setState(() => _loadingInsight = true);
    try {
      final data = await apiService.getExpenseInsights(monthYear: _selectedMonth);
      setState(() {
        _aiSummary = data['ai_summary'] ?? '';
        _loadingInsight = false;
      });
    } catch (e) {
      setState(() {
        _aiSummary = '⚠️ Could not load AI insights: $e';
        _loadingInsight = false;
      });
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
                  onRefresh: _loadCategories,
                  color: _primary,
                  child: CustomScrollView(
                    slivers: [
                      SliverAppBar(
                        backgroundColor: _surface,
                        pinned: true,
                        elevation: 0,
                        title: Row(children: [
                          const Icon(Icons.auto_graph, color: _primary, size: 22),
                          const SizedBox(width: 10),
                          Text('Expense Analysis',
                              style: GoogleFonts.inter(
                                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 17)),
                        ]),
                      ),
                      SliverToBoxAdapter(child: _buildMonthSelector()),
                      SliverToBoxAdapter(child: _buildStatsRow()),
                      SliverToBoxAdapter(child: _buildDonutCard()),
                      SliverToBoxAdapter(child: _buildCategoryList()),
                      SliverToBoxAdapter(child: _buildAIInsightCard()),
                      const SliverToBoxAdapter(child: SizedBox(height: 32)),
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
            onTap: () {
              setState(() { _selectedMonth = m; _aiSummary = ''; });
              _loadCategories();
            },
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

  Widget _buildStatsRow() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Expanded(child: _stat('Total Spent', '${_totalSpent.toStringAsFixed(0)} RON', _primary)),
          Expanded(child: _stat('Categories', '${_categories.length}', const Color(0xFFD29922))),
          Expanded(child: _stat('Top Spend', _topCategory, const Color(0xFFBC8CFF))),
        ],
      ),
    );
  }

  Widget _stat(String label, String value, Color color) => Column(
    children: [
      Text(value,
          style: GoogleFonts.inter(color: color, fontSize: 14, fontWeight: FontWeight.w700),
          maxLines: 1, overflow: TextOverflow.ellipsis),
      const SizedBox(height: 2),
      Text(label, style: GoogleFonts.inter(color: _muted, fontSize: 11)),
    ],
  );

  Widget _buildDonutCard() {
    if (_categories.isEmpty) return const SizedBox();
    final entries = _categories.entries.toList();

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 14, 16, 0),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _border),
      ),
      child: Column(
        children: [
          Text('Spending by Category',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(height: 20),
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                pieTouchData: PieTouchData(
                  touchCallback: (event, response) {
                    setState(() {
                      if (!event.isInterestedForInteractions ||
                          response == null ||
                          response.touchedSection == null) {
                        _touchedIndex = -1;
                        return;
                      }
                      _touchedIndex = response.touchedSection!.touchedSectionIndex;
                    });
                  },
                ),
                sections: entries.asMap().entries.map((e) {
                  final isTouched = e.key == _touchedIndex;
                  final color = _chartColors[e.key % _chartColors.length];
                  final pct = _totalSpent > 0 ? (e.value.value / _totalSpent * 100) : 0;
                  return PieChartSectionData(
                    value: e.value.value,
                    color: color,
                    radius: isTouched ? 90 : 75,
                    title: isTouched ? '${pct.toStringAsFixed(1)}%' : '',
                    titleStyle: GoogleFonts.inter(
                        color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700),
                    badgeWidget: !isTouched ? null : Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                          color: _bg, borderRadius: BorderRadius.circular(8)),
                      child: Text(e.value.key,
                          style: GoogleFonts.inter(color: color, fontSize: 10)),
                    ),
                    badgePositionPercentageOffset: 1.1,
                  );
                }).toList(),
                sectionsSpace: 2,
                centerSpaceRadius: 45,
                centerSpaceColor: _bg,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryList() {
    if (_categories.isEmpty) return const SizedBox();
    final entries = _categories.entries.toList();
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 14, 16, 0),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Breakdown',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          ...entries.asMap().entries.map((entry) {
            final i = entry.key;
            final c = entry.value;
            final pct = _totalSpent > 0 ? (c.value / _totalSpent * 100) : 0;
            final color = _chartColors[i % _chartColors.length];
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                children: [
                  Container(width: 10, height: 10,
                      decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                  const SizedBox(width: 10),
                  Expanded(child: Text(c.key,
                      style: GoogleFonts.inter(color: Colors.white, fontSize: 13))),
                  Text('${c.value.toStringAsFixed(0)} RON',
                      style: GoogleFonts.inter(
                          color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 38,
                    child: Text('${pct.toStringAsFixed(0)}%',
                        style: GoogleFonts.inter(color: _muted, fontSize: 12),
                        textAlign: TextAlign.right),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildAIInsightCard() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 14, 16, 0),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1F6FEB).withOpacity(0.15),
            _surface,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1F6FEB).withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('🤖', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Text('Tori\'s Analysis',
                  style: GoogleFonts.inter(
                      color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
              const Spacer(),
              if (!_loadingInsight)
                TextButton.icon(
                  icon: const Icon(Icons.auto_awesome, size: 14, color: _primary),
                  label: Text(_aiSummary.isEmpty ? 'Generate' : 'Refresh',
                      style: GoogleFonts.inter(color: _primary, fontSize: 12)),
                  onPressed: _loadInsight,
                ),
            ],
          ),
          const SizedBox(height: 12),
          if (_loadingInsight)
            const Center(
                child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(color: _primary, strokeWidth: 2),
            ))
          else if (_aiSummary.isEmpty)
            Text(
              'Tap "Generate" to get AI-powered spending insights for this month.',
              style: GoogleFonts.inter(color: _muted, fontSize: 13),
            )
          else
            MarkdownBody(
              data: _aiSummary,
              styleSheet: MarkdownStyleSheet(
                p: GoogleFonts.inter(color: Colors.white70, fontSize: 13, height: 1.5),
                listBullet: GoogleFonts.inter(color: Colors.white70, fontSize: 13),
                strong: GoogleFonts.inter(
                    color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
              ),
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
          const Icon(Icons.error_outline, color: _muted, size: 48),
          const SizedBox(height: 12),
          Text('Failed to load expenses', style: GoogleFonts.inter(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadCategories,
            style: ElevatedButton.styleFrom(backgroundColor: _primary),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
