import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';

class GenerativeWidgetBuilder {
  static Widget buildFromJson(String jsonString) {
    try {
      final Map<String, dynamic> data = jsonDecode(jsonString);
      final type = data['type'] as String?;

      switch (type) {
        case 'budget_slider':
          return BudgetSliderWidget(data: data);
        case 'receipt':
          return ReceiptWidget(data: data);
        case 'action_button':
          return ActionButtonWidget(data: data);
        default:
          return _errorWidget('Unknown widget type: $type');
      }
    } catch (e) {
      return _errorWidget('Error parsing widget: $e');
    }
  }

  static Widget _errorWidget(String msg) {
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF85149).withOpacity(0.1),
        border: Border.all(color: const Color(0xFFF85149)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(msg, style: GoogleFonts.inter(color: const Color(0xFFF85149))),
    );
  }
}

class BudgetSliderWidget extends StatefulWidget {
  final Map<String, dynamic> data;
  const BudgetSliderWidget({super.key, required this.data});

  @override
  State<BudgetSliderWidget> createState() => _BudgetSliderWidgetState();
}

class _BudgetSliderWidgetState extends State<BudgetSliderWidget> {
  late double _limit;
  bool _isSaving = false;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _limit = (widget.data['limit'] as num?)?.toDouble() ?? 1000.0;
  }

  Future<void> _saveBudget() async {
    setState(() {
      _isSaving = true;
      _saved = false;
    });
    try {
      final monthYear = "${DateTime.now().year}-${DateTime.now().month.toString().padLeft(2, '0')}";
      await apiService.createBudget(widget.data['category'] ?? 'General', monthYear, _limit);
      setState(() {
        _saved = true;
      });
    } catch (e) {
      // Handle error natively if needed
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final category = widget.data['category'] ?? 'General';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.tune, color: Color(0xFF58A6FF), size: 20),
              const SizedBox(width: 8),
              Text(
                'Adjust $category Budget',
                style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            'Limit: ${_limit.toStringAsFixed(0)} RON',
            style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 14),
          ),
          Slider(
            value: _limit,
            min: 0,
            max: 5000,
            divisions: 100,
            activeColor: const Color(0xFF58A6FF),
            inactiveColor: const Color(0xFF30363D),
            onChanged: (val) {
              setState(() {
                _limit = val;
                _saved = false;
              });
            },
          ),
          Align(
            alignment: Alignment.centerRight,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _saveBudget,
              style: ElevatedButton.styleFrom(
                backgroundColor: _saved ? const Color(0xFF238636) : const Color(0xFF1F6FEB),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _isSaving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Text(_saved ? 'Saved!' : 'Save Changes', style: GoogleFonts.inter(color: Colors.white)),
            ),
          )
        ],
      ),
    );
  }
}

class ReceiptWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  const ReceiptWidget({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final merchant = data['merchant'] ?? 'Unknown';
    final amount = (data['amount'] as num?)?.toDouble() ?? 0.0;
    final date = data['date'] ?? '';
    final category = data['category'] ?? 'Other';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: const Color(0xFF21262D),
                    radius: 16,
                    child: Text(merchant[0].toUpperCase(), style: GoogleFonts.inter(color: const Color(0xFF58A6FF), fontSize: 14, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 12),
                  Text(merchant, style: GoogleFonts.inter(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              Text('-${amount.toStringAsFixed(2)} RON', style: GoogleFonts.inter(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(color: Color(0xFF30363D), height: 1),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Date', style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 13)),
              Text(date, style: GoogleFonts.inter(color: Colors.white, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Category', style: GoogleFonts.inter(color: const Color(0xFF8B949E), fontSize: 13)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF3FB950).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(category, style: GoogleFonts.inter(color: const Color(0xFF3FB950), fontSize: 12)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ActionButtonWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  const ActionButtonWidget({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final label = data['label'] ?? 'Action';
    final action = data['action'] ?? '';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      width: double.infinity,
      child: ElevatedButton(
        onPressed: () async {
          if (action == 'sync_bank') {
            try {
              await apiService.syncBank();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bank synced successfully!')));
              }
            } catch (e) {
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error syncing: $e')));
              }
            }
          } else {
             ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Action $action not implemented yet.')));
          }
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF21262D),
          padding: const EdgeInsets.symmetric(vertical: 12),
          side: const BorderSide(color: Color(0xFF30363D)),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: Text(label, style: GoogleFonts.inter(color: const Color(0xFF58A6FF), fontSize: 15, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
