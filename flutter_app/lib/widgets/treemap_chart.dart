// lib/widgets/treemap_chart.dart
// A dependency-free squarified treemap chart.
//
// Tiles are laid out so that area ∝ value, using the squarified algorithm
// (Bruls, Huizing & van Wijk) which keeps rectangles close to square for
// readability. Drop-in replacement for pie/donut charts.

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_colors.dart';

class TreemapTile {
  final String label;
  final double value;
  final Color color;
  final String? sublabel;

  const TreemapTile({
    required this.label,
    required this.value,
    required this.color,
    this.sublabel,
  });
}

class _Placed {
  final TreemapTile tile;
  final Rect rect;
  _Placed(this.tile, this.rect);
}

class TreemapChart extends StatelessWidget {
  final List<TreemapTile> tiles;
  final double height;

  const TreemapChart({super.key, required this.tiles, this.height = 240});

  @override
  Widget build(BuildContext context) {
    final positive = tiles.where((t) => t.value > 0).toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    if (positive.isEmpty) {
      return SizedBox(
        height: height,
        child: Center(
          child: Text('No data',
              style: GoogleFonts.inter(color: AppColors.muted, fontSize: 12)),
        ),
      );
    }

    return SizedBox(
      height: height,
      child: LayoutBuilder(
        builder: (ctx, constraints) {
          final placed = _squarify(
            positive,
            constraints.maxWidth,
            constraints.maxHeight,
          );
          return Stack(
            children: [
              for (final p in placed)
                Positioned(
                  left: p.rect.left,
                  top: p.rect.top,
                  width: p.rect.width,
                  height: p.rect.height,
                  child: _buildTile(p),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildTile(_Placed p) {
    final r = p.rect;
    final t = p.tile;
    // Hide text on slivers too small to read.
    final showLabel = r.width >= 44 && r.height >= 26;
    final showSub = t.sublabel != null && r.width >= 56 && r.height >= 42;
    final onColor = _contrastColor(t.color);

    return Padding(
      padding: const EdgeInsets.all(1.5),
      child: Container(
        decoration: BoxDecoration(
          color: t.color,
          borderRadius: BorderRadius.circular(6),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 5),
        alignment: Alignment.topLeft,
        child: !showLabel
            ? null
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    t.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.inter(
                      color: onColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (showSub)
                    Text(
                      t.sublabel!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.inter(
                        color: onColor.withOpacity(0.85),
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                ],
              ),
      ),
    );
  }

  static Color _contrastColor(Color bg) {
    // Relative luminance → pick primary text or white for readability.
    final luminance =
        (0.299 * bg.red + 0.587 * bg.green + 0.114 * bg.blue) / 255.0;
    return luminance > 0.6 ? AppColors.textPrimary : Colors.white;
  }

  // ── Squarified treemap layout ────────────────────────────────────────────
  List<_Placed> _squarify(List<TreemapTile> tiles, double width, double height) {
    final out = <_Placed>[];
    if (width <= 0 || height <= 0) return out;

    final totalValue = tiles.fold<double>(0, (s, t) => s + t.value);
    final totalArea = width * height;
    // Scale each value to a pixel area.
    final areas = tiles.map((t) => t.value / totalValue * totalArea).toList();

    var x = 0.0, y = 0.0, w = width, h = height;
    final row = <int>[];
    var i = 0;

    double shortestSide() => math.min(w, h);

    while (i < tiles.length) {
      final candidate = [...row, i];
      if (row.isEmpty ||
          _worst(row, areas, shortestSide()) >=
              _worst(candidate, areas, shortestSide())) {
        row.add(i);
        i++;
      } else {
        final consumed = _layoutRow(row, areas, tiles, x, y, w, h, out);
        x = consumed.left;
        y = consumed.top;
        w = consumed.width;
        h = consumed.height;
        row.clear();
      }
    }
    if (row.isNotEmpty) {
      _layoutRow(row, areas, tiles, x, y, w, h, out);
    }
    return out;
  }

  // Returns the remaining rect as (dx, dy, width, height) packed in a Rect.
  Rect _layoutRow(
    List<int> row,
    List<double> areas,
    List<TreemapTile> tiles,
    double x,
    double y,
    double w,
    double h,
    List<_Placed> out,
  ) {
    final rowArea = row.fold<double>(0, (s, idx) => s + areas[idx]);
    if (w >= h) {
      // Lay row vertically along the left edge.
      final colW = rowArea / h;
      var cy = y;
      for (final idx in row) {
        final tileH = areas[idx] / colW;
        out.add(_Placed(tiles[idx], Rect.fromLTWH(x, cy, colW, tileH)));
        cy += tileH;
      }
      return Rect.fromLTWH(x + colW, y, w - colW, h);
    } else {
      // Lay row horizontally along the top edge.
      final rowH = rowArea / w;
      var cx = x;
      for (final idx in row) {
        final tileW = areas[idx] / rowH;
        out.add(_Placed(tiles[idx], Rect.fromLTWH(cx, y, tileW, rowH)));
        cx += tileW;
      }
      return Rect.fromLTWH(x, y + rowH, w, h - rowH);
    }
  }

  // Worst (max) aspect ratio produced by adding the row, given the side length.
  double _worst(List<int> row, List<double> areas, double side) {
    if (row.isEmpty || side <= 0) return double.infinity;
    var sum = 0.0, maxA = 0.0, minA = double.infinity;
    for (final idx in row) {
      final a = areas[idx];
      sum += a;
      if (a > maxA) maxA = a;
      if (a < minA) minA = a;
    }
    if (sum <= 0 || minA <= 0) return double.infinity;
    final side2 = side * side;
    final sum2 = sum * sum;
    return math.max((side2 * maxA) / sum2, sum2 / (side2 * minA));
  }
}
