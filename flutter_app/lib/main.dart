import 'package:flutter/material.dart';

void main() {
  runApp(const FinanceAdvisorApp());
}

class FinanceAdvisorApp extends StatelessWidget {
  const FinanceAdvisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Finance Advisor',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterialDesign: true,
      ),
      home: const DashboardPage(),
    );
  }
}

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Finance Advisor'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Icon(Icons.account_balance_wallet, size: 100, color: Colors.deepPurple),
            const SizedBox(height: 20),
            Text(
              'Welcome to your Personal Finance Advisor',
              style: Theme.of(context).textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 10),
            const Text('Start managing your budget today!'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        floatingActionButton: FloatingActionButton(onPressed: () {
          // TODO: Open a modal to add a new transaction
          showModalBottomSheet(
            context: context,
            builder: (context) =>
            const Padding(
              padding: EdgeInsets.all(32.0),
              child: Text('Add Transaction Form goes here'),
            ),
          );
        },
          tooltip: 'Add Transaction',
          child: const Icon(Icons.add),
        ),
        onPressed: () {},
        tooltip: 'Add Transaction',
        child: const Icon(Icons.add),
      ),
    );
  }
}
