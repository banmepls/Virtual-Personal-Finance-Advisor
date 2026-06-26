import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/api_service.dart';
import '../widgets/generative_ui.dart';

class ChatScreen extends StatefulWidget {
  final int userId;
  const ChatScreen({super.key, required this.userId});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, String>> _messages = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _scrollToBottom({bool animate = true}) {
    void jump() {
      if (!_scrollController.hasClients) return;
      final target = _scrollController.position.maxScrollExtent;
      if (animate) {
        _scrollController.animateTo(
          target,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      } else {
        _scrollController.jumpTo(target);
      }
    }

    // Markdown text and generative widgets settle their height across a few
    // layout passes, so maxScrollExtent grows after the first frame. Jump once
    // post-frame, then re-pin to the true bottom after content settles.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      jump();
      Future.delayed(const Duration(milliseconds: 200), jump);
      Future.delayed(const Duration(milliseconds: 450), jump);
    });
  }

  Future<void> _loadHistory() async {
    try {
      final history = await apiService.fetchHistory(widget.userId);
      if (!mounted) return;
      setState(() {
        for (var msg in history) {
          _messages.add({'role': msg['role'], 'content': msg['content']});
        }
      });
      // On first load, jump straight to the bottom (no scroll animation).
      _scrollToBottom(animate: false);
    } catch (e) {
      // Handle error gracefully
    }
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _controller.clear();
      _loading = true;
    });

    _scrollToBottom();
    try {
      final response = await apiService.chatWithTori(widget.userId, text);
      if (!mounted) return;
      setState(() {
        _messages.add({'role': 'assistant', 'content': response['response']});
        _loading = false;
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add({
          'role': 'assistant', 
          'content': 'I am sorry, I encountered an error. Please try again later.'
        });
        _loading = false;
      });
      _scrollToBottom();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFFFFFF),
        elevation: 0,
        title: Text(
          'Tori AI Advisor',
          style: GoogleFonts.inter(
            color: const Color(0xFF1F2328),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';
                return _buildChatBubble(msg['content']!, isUser);
              },
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF0969DA)),
              ),
            ),
          _buildSuggestions(),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildChatBubble(String content, bool isUser) {
    List<Widget> children = [];
    final regex = RegExp(r'```(?:widget|json)?\s*(\{.*?\})\s*```', dotAll: true);
    final matches = regex.allMatches(content);
    int lastMatchEnd = 0;

    for (final match in matches) {
      if (match.start > lastMatchEnd) {
        final text = content.substring(lastMatchEnd, match.start).trim();
        if (text.isNotEmpty) {
          children.add(_buildMarkdownText(text));
        }
      }
      final jsonStr = match.group(1) ?? '';
      if (jsonStr.isNotEmpty) {
        children.add(GenerativeWidgetBuilder.buildFromJson(jsonStr));
      }
      lastMatchEnd = match.end;
    }

    if (lastMatchEnd < content.length) {
      final text = content.substring(lastMatchEnd).trim();
      if (text.isNotEmpty) {
        children.add(_buildMarkdownText(text));
      }
    }

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF0969DA) : const Color(0xFFEEF1F5),
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? const Radius.circular(0) : const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(0),
          ),
          border: Border.all(color: const Color(0xFFD0D7DE)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: children.isEmpty ? [_buildMarkdownText(content)] : children,
        ),
      ),
    );
  }

  Widget _buildMarkdownText(String text) {
    return MarkdownBody(
      data: text,
      styleSheet: MarkdownStyleSheet(
        p: GoogleFonts.inter(color: const Color(0xFF1F2328), fontSize: 15),
        strong: GoogleFonts.inter(color: const Color(0xFF1F2328), fontSize: 15, fontWeight: FontWeight.bold),
        listBullet: GoogleFonts.inter(color: const Color(0xFF1F2328), fontSize: 15),
      ),
    );
  }

  Widget _buildSuggestions() {
    final List<String> suggestions = [
      "Adjust my Dining budget to 500 RON",
      "Show me my recent transactions",
      "Did I overspend this month?",
      "Set a new budget for Groceries",
    ];

    return Container(
      height: 40,
      margin: const EdgeInsets.only(bottom: 12),
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        scrollDirection: Axis.horizontal,
        itemCount: suggestions.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final text = suggestions[index];
          return ActionChip(
            label: Text(text, style: GoogleFonts.inter(color: const Color(0xFF1F2328), fontSize: 13)),
            backgroundColor: const Color(0xFFEEF1F5),
            side: const BorderSide(color: Color(0xFFD0D7DE)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            onPressed: () {
              _controller.text = text;
              _controller.selection = TextSelection.fromPosition(TextPosition(offset: text.length));
            },
          );
        },
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFFFF),
        border: Border(top: BorderSide(color: const Color(0xFFD0D7DE))),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              style: GoogleFonts.inter(color: const Color(0xFF1F2328)),
              decoration: InputDecoration(
                hintText: 'Ask Tori something...',
                hintStyle: GoogleFonts.inter(color: const Color(0xFF656D76)),
                border: InputBorder.none,
              ),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Color(0xFF0969DA)),
            onPressed: _sendMessage,
          ),
        ],
      ),
    );
  }
}
