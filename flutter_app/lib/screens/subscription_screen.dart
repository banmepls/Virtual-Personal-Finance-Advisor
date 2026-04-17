import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/bank_model.dart';
import '../services/api_service.dart';

class SubscriptionScreen extends StatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  State<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends State<SubscriptionScreen> {
  List<Subscription> _subscriptions = [];
  bool _loading = true;
  String? _error;
  double get _monthlyTotal =>
      _subscriptions.fold(0, (sum, s) => sum + s.amount);

  static const _primary = Color(0xFF58A6FF);
  static const _surface = Color(0xFF161B22);
  static const _bg = Color(0xFF0D1117);
  static const _border = Color(0xFF30363D);
  static const _muted = Color(0xFF8B949E);
  static const _purple = Color(0xFFBC8CFF);
  static const _red = Color(0xFFF85149);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await apiService.getSubscriptions();
      setState(() {
        _subscriptions = data
            .map((s) => Subscription.fromJson(s as Map<String, dynamic>))
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
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
                          const Icon(Icons.subscriptions, color: _purple, size: 22),
                          const SizedBox(width: 10),
                          Text('Subscriptions',
                              style: GoogleFonts.inter(
                                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 17)),
                        ]),
                      ),
                      SliverToBoxAdapter(child: _buildSummaryCard()),
                      if (_subscriptions.isEmpty)
                        SliverToBoxAdapter(child: _buildEmpty())
                      else
                        SliverList(
                          delegate: SliverChildBuilderDelegate(
                            (ctx, i) => _buildSubCard(_subscriptions[i]),
                            childCount: _subscriptions.length,
                          ),
                        ),
                      const SliverToBoxAdapter(child: SizedBox(height: 24)),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSummaryCard() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _purple.withOpacity(0.2),
            const Color(0xFF161B22),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _purple.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Total Monthly Subscriptions',
                  style: GoogleFonts.inter(color: Colors.white70, fontSize: 13)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _purple.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text('${_subscriptions.length} active',
                    style: GoogleFonts.inter(
                        color: _purple, fontSize: 12, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${_monthlyTotal.toStringAsFixed(2)} RON/mo',
            style: GoogleFonts.inter(
                color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 4),
          Text(
            '≈ ${(_monthlyTotal * 12).toStringAsFixed(0)} RON/year',
            style: GoogleFonts.inter(color: Colors.white54, fontSize: 13),
          ),
          const SizedBox(height: 12),
          Text(
            '💡 Review regularly — unused subscriptions cost money!',
            style: GoogleFonts.inter(color: Colors.white60, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildSubCard(Subscription sub) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: _purple.withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.repeat, color: _purple, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(sub.merchant,
                    style: GoogleFonts.inter(
                        color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                const SizedBox(height: 3),
                Row(
                  children: [
                    _chip(sub.category, _purple),
                    const SizedBox(width: 6),
                    _chip(sub.frequency, const Color(0xFF8B949E)),
                    const SizedBox(width: 6),
                    if (sub.lastCharge.isNotEmpty)
                      Text('Last: ${sub.lastCharge}',
                          style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 10)),
                  ],
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${sub.amount.toStringAsFixed(2)}',
                style: GoogleFonts.inter(
                    color: _red, fontSize: 14, fontWeight: FontWeight.w700),
              ),
              Text('RON/mo',
                  style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 10)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _chip(String text, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(
      color: color.withOpacity(0.12),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Text(text,
        style: GoogleFonts.inter(color: color, fontSize: 10, fontWeight: FontWeight.w600)),
  );

  Widget _buildEmpty() {
    return Padding(
      padding: const EdgeInsets.all(40),
      child: Column(
        children: [
          const Icon(Icons.check_circle_outline, color: Color(0xFF3FB950), size: 56),
          const SizedBox(height: 16),
          Text('No Subscriptions Detected',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 17, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('Sync your bank transactions to auto-detect recurring charges.',
              style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 13),
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
          const Icon(Icons.error_outline, color: Color(0xFF8B949E), size: 48),
          const SizedBox(height: 12),
          Text('Failed to load subscriptions',
              style: GoogleFonts.inter(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _load,
            style: ElevatedButton.styleFrom(backgroundColor: _primary),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
