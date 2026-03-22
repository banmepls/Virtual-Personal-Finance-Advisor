import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  final int userId;
  const ChatScreen({super.key, required this.userId});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, String>> _messages = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final history = await apiService.fetchHistory(widget.userId);
      setState(() {
        for (var msg in history) {
          _messages.add({'role': msg['role'], 'content': msg['content']});
        }
      });
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

    try {
      final response = await apiService.chatWithTori(widget.userId, text);
      setState(() {
        _messages.add({'role': 'assistant', 'content': response['response']});
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'assistant', 
          'content': 'I am sorry, I encountered an error. Please try again later.'
        });
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        title: Text(
          'Tori AI Advisor',
          style: GoogleFonts.inter(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
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
                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF58A6FF)),
              ),
            ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildChatBubble(String content, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF1F6FEB) : const Color(0xFF21262D),
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? const Radius.circular(0) : const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(0),
          ),
          border: Border.all(color: const Color(0xFF30363D)),
        ),
        child: MarkdownBody(
          data: content,
          styleSheet: MarkdownStyleSheet(
            p: GoogleFonts.inter(color: Colors.white, fontSize: 15),
            strong: GoogleFonts.inter(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
            listBullet: GoogleFonts.inter(color: Colors.white, fontSize: 15),
          ),
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        border: Border(top: BorderSide(color: const Color(0xFF30363D))),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              style: GoogleFonts.inter(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Ask Tori something...',
                hintStyle: GoogleFonts.inter(color: const Color(0xFF8B949E)),
                border: InputBorder.none,
              ),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Color(0xFF58A6FF)),
            onPressed: _sendMessage,
          ),
        ],
      ),
    );
  }
}
