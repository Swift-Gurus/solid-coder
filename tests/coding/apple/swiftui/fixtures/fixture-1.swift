import SwiftUI

/**
 solid-name: DashboardViewModel
 solid-category: model
 solid-description: Supplies dashboard state while intentionally mixing UI state with background-safe work for workflow validation.
 */
@MainActor
final class DashboardViewModel {
    var rows: [String] = []

    func load() async throws {
        rows = try await fetchRows()
    }

    func fetchRows() async throws -> [String] {
        ["Revenue", "Retention", "Conversion"]
    }
}

/**
 solid-name: DashboardView
 solid-category: view
 solid-description: Exercises every SwiftUI review measurement in one deterministic fixture.
 */
struct DashboardView: View {
    let viewModel = DashboardViewModel()
    @State private var query = ""

    var body: some View {
        VStack {
            HStack {
                Text("Dashboard")
                    .font(.headline)
                    .padding()
                Image(systemName: "chart.bar")
                Button("Reload") {
                    Task {
                        try? await viewModel.load()
                    }
                }
            }
            .accessibilityIdentifier("dashboard-header")

            TextField("Filter", text: $query)
                .frame(width: 240, height: 44)
            Text(filteredRows.joined(separator: ", "))
            PreviewOnlyBadge()
        }
    }

    var filteredRows: [String] {
        viewModel.rows.filter { query.isEmpty || $0.contains(query) }
    }
}

/**
 solid-name: PreviewOnlyBadge
 solid-category: view
 solid-description: Represents an orphaned preview-only helper view for repository-evidence validation.
 */
struct PreviewOnlyBadge: View {
    var body: some View {
        Text("Preview")
    }
}
