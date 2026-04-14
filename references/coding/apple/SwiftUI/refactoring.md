---
name: swiftui-refactoring
type: refactoring
---

# SwiftUI Best Practices

> A View should be a function of its state — nothing more.
---

## SwiftUI Refactoring Approaches

This framework provides examples of how to refactor SwiftUI views for body complexity and view purity violations.

---

## Refactoring Depth

All violations are SEVERE. Extract subviews for body complexity, move logic to ViewModel for purity violations, extract named variables for long modifier chains.

---

## Extract Subview (SUI-1: Body Complexity)

The primary fix for deep nesting. Extract coherent sections of `body` into named subviews.

```swift
// BEFORE: Nesting depth 6, 12 expressions
struct OrderDetailView: View {
    let order: Order

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                HStack {
                    VStack(alignment: .leading) {
                        Text(order.title).font(.headline)
                        Text(order.subtitle).foregroundColor(.secondary)
                        HStack {
                            ForEach(order.tags) { tag in
                                VStack {
                                    Image(systemName: tag.icon)
                                    Text(tag.name).font(.caption)
                                }
                                .padding(4)
                                .background(Color.gray.opacity(0.2))
                                .cornerRadius(4)
                            }
                        }
                    }
                    Spacer()
                    Text(order.price).font(.title2)
                }
                Divider()
                ForEach(order.items) { item in
                    ItemRow(item: item)
                }
                Button("Checkout") { checkout() }
            }
            .padding()
        }
    }
}

// AFTER: Max nesting 3, each subview is focused
struct OrderDetailView: View {
    let order: Order

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                OrderHeaderView(order: order)
                Divider()
                OrderItemsView(items: order.items)
                Button("Checkout") { checkout() }
            }
            .padding()
        }
    }
}

struct OrderHeaderView: View {
    let order: Order

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(order.title).font(.headline)
                Text(order.subtitle).foregroundColor(.secondary)
                TagListView(tags: order.tags)
            }
            Spacer()
            Text(order.price).font(.title2)
        }
    }
}

struct TagListView: View {
    let tags: [Tag]

    var body: some View {
        HStack {
            ForEach(tags) { tag in
                Label(tag.name, systemImage: tag.icon)
                    .font(.caption)
                    .padding(4)
                    .background(Color.gray.opacity(0.2))
                    .cornerRadius(4)
            }
        }
    }
}

struct OrderItemsView: View {
    let items: [OrderItem]

    var body: some View {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}
```

**Key:** Each extracted subview has a single visual concern and takes only the data it needs.

---

## Extract Helper View — Conditional Sections

When body complexity comes from multiple conditional branches, extract each branch.

```swift
// BEFORE: complex conditional in body adds nesting + expressions
var body: some View {
    VStack {
        if let error = viewModel.error {
            VStack {
                Image(systemName: "exclamationmark.triangle")
                Text(error.localizedDescription)
                Button("Retry") { viewModel.retry() }
            }
        } else if viewModel.isLoading {
            ProgressView()
        } else {
            // actual content (20+ lines)
        }
    }
}

// AFTER: each state is a subview
var body: some View {
    VStack {
        switch viewModel.state {
        case .error(let error): ErrorView(error: error, onRetry: viewModel.retry)
        case .loading: ProgressView()
        case .loaded: ContentView(data: viewModel.data)
        }
    }
}
```

---

## Extract ViewModifier — Repeated Styling

When expression count is high due to repeated modifier chains, extract into a ViewModifier.

```swift
// BEFORE: repeated styling inflates body
Text("Title")
    .font(.headline)
    .foregroundColor(.primary)
    .padding(.horizontal, 16)
    .padding(.vertical, 8)
    .background(Color.blue.opacity(0.1))
    .cornerRadius(8)

// AFTER: extracted modifier
struct CardTitle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .font(.headline)
            .foregroundColor(.primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color.blue.opacity(0.1))
            .cornerRadius(8)
    }
}

Text("Title").modifier(CardTitle())
```

---

## Extract Named Variable (SUI-3: Modifier Chain Length)

The primary fix for long modifier chains on nested views. Extract the view + its modifiers into a named computed property.

```swift
// BEFORE: nested child views with 3-4 modifiers inline
struct FollowerCountBadge: View {
    let count: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "person.2.fill")
                .foregroundColor(.blue)
            Text(count)
                .font(.subheadline)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.1))
        .cornerRadius(16)
    }
}

// AFTER: nested children extracted to named vars
struct FollowerCountBadge: View {
    let count: String

    var body: some View {
        HStack(spacing: 4) {
            icon
            countText
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.1))
        .cornerRadius(16)
    }

    private var icon: some View {
        Image(systemName: "person.2.fill")
            .foregroundColor(.blue)
    }

    private var countText: some View {
        Text(count)
            .font(.subheadline)
            .fontWeight(.medium)
    }
}
```

**Key:** Only nested child views inside closures need extraction. The top-level modifier chain on the `HStack` itself (`.padding`, `.background`, `.cornerRadius`) is fine — it's the outermost return value, not a nested child.

**When modifier chains are repeated across views**, consider extracting a `ViewModifier` instead (see Extract ViewModifier pattern below).

---

## Move to ViewModel (SUI-2: View Purity)

The primary fix for impure views. Move all business logic, formatting, data fetching, and computation out of the view into a ViewModel.

```swift
// BEFORE: View does formatting, validation, and API calls (4 IMPURE methods)
struct InvoiceView: View {
    @State private var invoice: Invoice
    @State private var isSending = false

    var body: some View {
        VStack {
            Text(formattedTotal)
            Text(dueDateString)
            if isOverdue { Text("OVERDUE").foregroundColor(.red) }
            Button("Send") { sendInvoice() }
                .disabled(isSending)
        }
    }

    // IMPURE (FORMAT)
    private var formattedTotal: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = invoice.locale
        return formatter.string(from: NSNumber(value: invoice.total)) ?? ""
    }

    // IMPURE (FORMAT)
    private var dueDateString: String {
        let fmt = DateFormatter()
        fmt.dateStyle = .medium
        return fmt.string(from: invoice.dueDate)
    }

    // IMPURE (COMPUTE)
    private var isOverdue: Bool {
        invoice.dueDate < Date() && invoice.status != .paid
    }

    // IMPURE (DATA_FETCH)
    private func sendInvoice() {
        isSending = true
        Task {
            await APIClient.shared.send(invoice)
            isSending = false
        }
    }
}

// AFTER: View is pure, ViewModel owns all logic
@Observable
final class InvoiceViewModel {
    let invoice: Invoice
    var isSending = false

    init(invoice: Invoice) { self.invoice = invoice }

    var formattedTotal: String {
        invoice.total.formatted(.currency(code: invoice.currencyCode))
    }

    var dueDateString: String {
        invoice.dueDate.formatted(date: .abbreviated, time: .omitted)
    }

    var isOverdue: Bool {
        invoice.dueDate < Date() && invoice.status != .paid
    }

    func send() async {
        isSending = true
        await APIClient.shared.send(invoice)
        isSending = false
    }
}

struct InvoiceView: View {
    @State private var viewModel: InvoiceViewModel

    var body: some View {
        VStack {
            Text(viewModel.formattedTotal)
            Text(viewModel.dueDateString)
            if viewModel.isOverdue { Text("OVERDUE").foregroundColor(.red) }
            Button("Send") { Task { await viewModel.send() } }
                .disabled(viewModel.isSending)
        }
    }
}
```

**Key:** The view's only job is binding ViewModel outputs to UI elements. All formatting, computation, validation, and data access live in the ViewModel.

**After refactoring:**
- `InvoiceView`: 0 IMPURE → COMPLIANT
- `InvoiceViewModel`: not a View — SUI-2 does not apply (SRP/OCP handle it)

---

## Two-Way Bindings with Protocol-Constrained ViewModels (SUI-4)

When a view needs `$vm.property` bindings (TextField, Toggle, Picker, etc.) after refactoring to protocol-constrained generics, use a **local `@Bindable` wrap** — never manual `Binding(get:set:)`.

```swift
// State protocol exposes get set for bindable properties
protocol SettingsState: Observable {
    var name: String { get set }
    var notificationsEnabled: Bool { get set }
}

protocol SettingsActions {
    func save()
}

struct SettingsView<VM: SettingsState & SettingsActions>: View {
    var vm: VM

    var body: some View {
        @Bindable var bindable = vm  // local wrap for $ projection
        Form {
            TextField("Name", text: $bindable.name)
            Toggle("Notifications", isOn: $bindable.notificationsEnabled)
            Button("Save") { vm.save() }
        }
    }
}
```

**Key:** `@Bindable` works with protocol-constrained generics because the `Observable` conformance is guaranteed by the constraint. The local `@Bindable var bindable = vm` inside `body` gives access to the `$` projection. Manual `Binding(get:set:)` is a code smell with `@Observable` — it bypasses the observation system.
