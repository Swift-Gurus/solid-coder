// COMPLIANT: View depends on non-Observable protocol — plain protocol type, no generic
// SUI-4: Protocol-typed property without generic → COMPLIANT (protocol does not extend Observable)
//
// Use this pattern when the view reads data once and doesn't need reactive updates,
// or when the dependency only provides actions (callbacks, navigation triggers).

protocol SummaryProviding {
    var title: String { get }
    var items: [String] { get }
}

protocol SummaryActions {
    func onItemTapped(_ item: String)
    func onDismiss()
}

struct SummaryView: View {
    let dataSource: SummaryProviding   // plain protocol — no generic needed
    let actions: SummaryActions         // plain protocol — no generic needed

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(dataSource.title)
                .font(.headline)
            ForEach(dataSource.items, id: \.self) { item in
                Button(item) { actions.onItemTapped(item) }
            }
            Button("Done") { actions.onDismiss() }
        }
    }
}

// No @Observable needed — data is read once, view doesn't observe changes
struct StaticSummary: SummaryProviding {
    let title: String
    let items: [String]
}
