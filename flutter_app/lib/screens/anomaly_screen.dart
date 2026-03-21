import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/portfolio_model.dart';
import '../models/anomaly_model.dart';
import '../services/api_service.dart';

class AnomalyScreen extends StatefulWidget {
  final List<PortfolioPosition> positions;
  const AnomalyScreen({super.key, required this.positions});

  @override
  State<AnomalyScreen> createState() => _AnomalyScreenState();
}

class _AnomalyScreenState extends State<AnomalyScreen> {
  AnomalyResult? _result;
  bool _loading = false;
  String? _error;

  Future<void> _analyze() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final positionsPayload = widget.positions
          .map((p) => {
                'instrument_id': p.instrumentId,
                'quantity': p.quantity,
                'avg_buy_price': p.avgBuyPrice,
                'current_value': p.currentValue,
                'unrealized_pnl': p.unrealizedPnl,
              })
          .toList();

      final data = await apiService.analyzePortfolio(positionsPayload);
      setState(() {
        _result = AnomalyResult.fromJson(data);
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
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Anomaly Detection',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(
            'Ensemble of Isolation Forest + Autoencoder + One-Class SVM',
            style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 12),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _loading ? null : _analyze,
              icon: _loading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Icon(Icons.radar),
              label: Text(_loading ? 'Analyzing...' : 'Analyze Portfolio'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1F6FEB),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF85149).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFF85149).withOpacity(0.4)),
              ),
              child: Text(_error!,
                  style: GoogleFonts.inter(
                      color: const Color(0xFFF85149), fontSize: 13)),
            ),
          ],
          if (_result != null) ...[
            const SizedBox(height: 20),
            _buildVerdictCard(_result!),
            const SizedBox(height: 12),
            _buildModelScores(_result!),
          ],
        ],
      ),
    );
  }

  Widget _buildVerdictCard(AnomalyResult r) {
    final isAnomaly = r.isAnomaly;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isAnomaly
              ? [
                  const Color(0xFFF85149).withOpacity(0.2),
                  const Color(0xFF161B22)
                ]
              : [
                  const Color(0xFF3FB950).withOpacity(0.2),
                  const Color(0xFF161B22)
                ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isAnomaly
              ? const Color(0xFFF85149).withOpacity(0.5)
              : const Color(0xFF3FB950).withOpacity(0.5),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isAnomaly ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                color: isAnomaly ? const Color(0xFFF85149) : const Color(0xFF3FB950),
                size: 28,
              ),
              const SizedBox(width: 10),
              Text(
                isAnomaly ? 'ANOMALY DETECTED' : 'PORTFOLIO NORMAL',
                style: GoogleFonts.inter(
                  color: isAnomaly ? const Color(0xFFF85149) : const Color(0xFF3FB950),
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildScoreBar(
              'Ensemble Score', r.weightedAvgScore, const Color(0xFF58A6FF)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildBadge('Confidence: ${r.confidence}',
                  _confidenceColor(r.confidence)),
              _buildBadge(
                  'Score: ${(r.weightedAvgScore * 100).toStringAsFixed(1)}%',
                  const Color(0xFF8B949E)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildModelScores(AnomalyResult r) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Model Breakdown',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          _buildModelRow('🌲 Isolation Forest', r.isolationScore, 0.35),
          const SizedBox(height: 10),
          _buildModelRow('🔄 Auto-Encoder', r.autoencoderMse, 0.40),
          const SizedBox(height: 10),
          _buildModelRow('⚙ One-Class SVM', r.svmScore, 0.25),
        ],
      ),
    );
  }

  Widget _buildModelRow(String name, double score, double weight) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(name,
                style: GoogleFonts.inter(
                    color: const Color(0xFF8B949E), fontSize: 12)),
            Text(
              '${(score * 100).toStringAsFixed(1)}%  (weight: ${(weight * 100).toInt()}%)',
              style: GoogleFonts.inter(
                  color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        const SizedBox(height: 4),
        _buildScoreBar('', score, _scoreColor(score)),
      ],
    );
  }

  Widget _buildScoreBar(String label, double score, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label.isNotEmpty)
          Text(label,
              style: GoogleFonts.inter(
                  color: const Color(0xFF8B949E), fontSize: 12)),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: score.clamp(0.0, 1.0),
            backgroundColor: const Color(0xFF21262D),
            color: color,
            minHeight: 8,
          ),
        ),
      ],
    );
  }

  Widget _buildBadge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(label,
          style: GoogleFonts.inter(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }

  Color _scoreColor(double score) {
    if (score < 0.33) return const Color(0xFF3FB950);
    if (score < 0.66) return const Color(0xFFD29922);
    return const Color(0xFFF85149);
  }

  Color _confidenceColor(String confidence) {
    switch (confidence) {
      case 'HIGH':
        return const Color(0xFF3FB950);
      case 'MEDIUM':
        return const Color(0xFFD29922);
      default:
        return const Color(0xFF8B949E);
    }
  }
}
