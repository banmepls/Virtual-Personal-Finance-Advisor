# Fix UI Overflows and Lifecycle Bugs

The goal is to resolve multiple UI rendering issues (overflows) and a runtime crash (setState after dispose) identified in the application logs.

## Proposed Changes

### UI Fixes (Overflows)

---

#### [bank_screen.dart](file:///C:/GITHUB/Virtual-Personal-Finance-Advisor/flutter_app/lib/screens/bank_screen.dart)

- Fix overflow in `_buildTransactionTile`. The inner `Row` containing the category tag and booking date overflows on narrow screens.
- **Change**: Wrap the category `Container` and/or the date `Text` in `Flexible` and add `overflow: TextOverflow.ellipsis` where appropriate.

```diff
- Row(
-   children: [
-     Container(
-       // ... category tag
-     ),
+ Row(
+   children: [
+     Flexible(
+       child: Container(
+         // ... category tag
+         child: Text(tx.category,
+             overflow: TextOverflow.ellipsis,
+             // ...
+         ),
+       ),
+     ),
```

---

#### [anomaly_screen.dart](file:///C:/GITHUB/Virtual-Personal-Finance-Advisor/flutter_app/lib/screens/anomaly_screen.dart)

- Fix bottom overflow when analysis results are displayed.
- Fix "setState() called after dispose()" crash in `_analyze`.
- **Changes**:
    - Wrap the main `Column` in a `SingleChildScrollView`.
    - Add `if (!mounted) return;` checks before all `setState` calls that occur after `await` operations.

---

#### [subscription_screen.dart](file:///C:/GITHUB/Virtual-Personal-Finance-Advisor/flutter_app/lib/screens/subscription_screen.dart)

- Proactively fix potential overflows in subscription tiles.
- **Change**: Ensure the merchant name and amount don't collide by using `Flexible` and proper alignment.

---

### Logic Fixes (Stability)

#### [chat_screen.dart](file:///C:/GITHUB/Virtual-Personal-Finance-Advisor/flutter_app/lib/screens/chat_screen.dart)

- Add `mounted` checks in `_loadHistory` and `_sendMessage` to prevent crashes if the user navigates away while Tori is typing.

## Verification Plan

### Manual Verification
- **Overflow Check**: Use the Flutter Inspector or a small screen emulator (e.g., Nexus 5) to verify that transaction tiles and the Anomaly screen no longer show "yellow and black striped" patterns.
- **Lifecycle Check**: Open the Anomaly screen, start an analysis, and immediately switch to another tab or close the screen. Verify that no "setState() called after dispose()" error appears in the console.
- **Scroll Check**: Verify that the Anomaly screen can be scrolled when results are visible.
