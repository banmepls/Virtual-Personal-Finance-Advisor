class PortfolioPosition {
  final int instrumentId;
  final String symbol;
  final String name;
  final String assetClass;
  final double quantity;
  final double avgBuyPrice;
  final double currentPrice;
  final double currentValue;
  final double unrealizedPnl;
  final double unrealizedPnlPercent;

  const PortfolioPosition({
    required this.instrumentId,
    required this.symbol,
    required this.name,
    required this.assetClass,
    required this.quantity,
    required this.avgBuyPrice,
    required this.currentPrice,
    required this.currentValue,
    required this.unrealizedPnl,
    required this.unrealizedPnlPercent,
  });

  factory PortfolioPosition.fromJson(Map<String, dynamic> json) {
    return PortfolioPosition(
      instrumentId: (json['instrument_id'] ?? json['instrumentId'] ?? 0) as int,
      symbol: (json['symbol'] ?? 'N/A') as String,
      name: (json['name'] ?? 'Unknown') as String,
      assetClass: (json['asset_class'] ?? json['assetClass'] ?? 'Unknown') as String,
      quantity: _toDouble(json['quantity']),
      avgBuyPrice: _toDouble(json['avgBuyPrice'] ?? json['avg_buy_price']),
      currentPrice: _toDouble(json['currentPrice'] ?? json['current_price']),
      currentValue: _toDouble(json['currentValue'] ?? json['current_value']),
      unrealizedPnl: _toDouble(json['unrealizedPnL'] ?? json['unrealized_pnl']),
      unrealizedPnlPercent: _toDouble(
          json['unrealizedPnLPercent'] ?? json['unrealized_pnl_percent']),
    );
  }

  static double _toDouble(dynamic val) {
    if (val == null) return 0.0;
    if (val is double) return val;
    if (val is int) return val.toDouble();
    return double.tryParse(val.toString()) ?? 0.0;
  }

  bool get isProfit => unrealizedPnl >= 0;
}

class Portfolio {
  final String username;
  final double totalPortfolioValue;
  final double totalPnL;
  final double totalPnLPercent;
  final List<PortfolioPosition> positions;

  const Portfolio({
    required this.username,
    required this.totalPortfolioValue,
    required this.totalPnL,
    required this.totalPnLPercent,
    required this.positions,
  });

  factory Portfolio.fromJson(Map<String, dynamic> json) {
    final rawPositions = json['positions'] as List<dynamic>? ?? [];
    return Portfolio(
      username: (json['username'] ?? '') as String,
      totalPortfolioValue:
          PortfolioPosition._toDouble(json['totalPortfolioValue']),
      totalPnL: PortfolioPosition._toDouble(json['totalPnL']),
      totalPnLPercent: PortfolioPosition._toDouble(json['totalPnLPercent']),
      positions: rawPositions
          .map((p) => PortfolioPosition.fromJson(p as Map<String, dynamic>))
          .toList(),
    );
  }
}
