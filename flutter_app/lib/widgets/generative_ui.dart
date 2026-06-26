import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

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
        color: AppColors.red.withOpacity(0.1),
        border: Border.all(color: AppColors.red),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(msg, style: GoogleFonts.inter(color: AppColors.red)),
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
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.tune, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Text(
                'Adjust $category Budget',
                style: GoogleFonts.inter(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            'Limit: ${_limit.toStringAsFixed(0)} RON',
            style: GoogleFonts.inter(color: AppColors.textSecondary, fontSize: 14),
          ),
          Slider(
            value: _limit,
            min: 0,
            max: 5000,
            divisions: 100,
            activeColor: AppColors.primary,
            inactiveColor: AppColors.border,
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
                backgroundColor: _saved ? AppColors.green : AppColors.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _isSaving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Text(_saved ? 'Saved!' : 'Save Changes', style: GoogleFonts.inter()),
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
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
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
                    backgroundColor: AppColors.chipBg,
                    radius: 16,
                    child: Text(merchant[0].toUpperCase(), style: GoogleFonts.inter(color: AppColors.primary, fontSize: 14, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 12),
                  Text(merchant, style: GoogleFonts.inter(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              Text('-${amount.toStringAsFixed(2)} RON', style: GoogleFonts.inter(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(color: AppColors.border, height: 1),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Date', style: GoogleFonts.inter(color: AppColors.textSecondary, fontSize: 13)),
              Text(date, style: GoogleFonts.inter(color: AppColors.textPrimary, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Category', style: GoogleFonts.inter(color: AppColors.textSecondary, fontSize: 13)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(category, style: GoogleFonts.inter(color: AppColors.green, fontSize: 12)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ActionButtonWidget extends StatefulWidget {
  final Map<String, dynamic> data;
  const ActionButtonWidget({super.key, required this.data});

  @override
  State<ActionButtonWidget> createState() => _ActionButtonWidgetState();
}

class _ActionButtonWidgetState extends State<ActionButtonWidget> {
  bool _running = false;
  bool _done = false;

  Future<void> _run() async {
    final action = widget.data['action'] ?? '';
    setState(() {
      _running = true;
      _done = false;
    });
    String message;
    Color color = const Color(0xFF238636);
    try {
      if (action == 'sync_bank') {
        final result = await apiService.syncBank();
        // Surface the real result so the user knows what happened.
        final synced = result['synced'] ?? 0;
        message = synced == 0
            ? '✅ Already up to date — no new transactions.'
            : '✅ Synced $synced new transaction(s).';
      } else {
        message = 'Action "$action" is not available.';
        color = const Color(0xFFD29922);
      }
      if (mounted) setState(() => _done = true);
    } catch (e) {
      message = 'Could not complete the action. Please try again.';
      color = const Color(0xFFF85149);
    }
    if (mounted) {
      setState(() => _running = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: color),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final label = widget.data['label'] ?? 'Action';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _running ? null : _run,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.chipBg,
          disabledBackgroundColor: AppColors.chipBg,
          padding: const EdgeInsets.symmetric(vertical: 12),
          side: const BorderSide(color: AppColors.border),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: _running
            ? Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppColors.primary)),
                  const SizedBox(width: 10),
                  Text('Working…',
                      style: GoogleFonts.inter(
                          color: AppColors.primary,
                          fontSize: 15,
                          fontWeight: FontWeight.bold)),
                ],
              )
            : Text(_done ? '✓ $label' : label,
                style: GoogleFonts.inter(
                    color: AppColors.primary,
                    fontSize: 15,
                    fontWeight: FontWeight.bold)),
      ),
    );
  }
}
