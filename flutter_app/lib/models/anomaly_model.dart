class AnomalyResult {
  final double isolationScore;
  final double autoencoderMse;
  final double svmScore;
  final double weightedAvgScore;
  final bool isAnomaly;
  final String confidence;
  final String notes;

  const AnomalyResult({
    required this.isolationScore,
    required this.autoencoderMse,
    required this.svmScore,
    required this.weightedAvgScore,
    required this.isAnomaly,
    required this.confidence,
    required this.notes,
  });

  factory AnomalyResult.fromJson(Map<String, dynamic> json) {
    return AnomalyResult(
      isolationScore: _d(json['isolation_score']),
      autoencoderMse: _d(json['autoencoder_mse']),
      svmScore: _d(json['svm_score']),
      weightedAvgScore: _d(json['weighted_avg_score']),
      isAnomaly: json['is_anomaly'] as bool? ?? false,
      confidence: json['confidence'] as String? ?? 'LOW',
      notes: json['notes'] as String? ?? '',
    );
  }

  static double _d(dynamic v) {
    if (v == null) return 0.0;
    if (v is double) return v;
    if (v is int) return v.toDouble();
    return double.tryParse(v.toString()) ?? 0.0;
  }
}
