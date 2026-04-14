// SUI-9 COMPLIANT: Correct actor isolation patterns

import SwiftUI

// --- CASE 1: Protocol-level @MainActor is COMPLIANT ---
// All production conformers (AppStateManager) are @MainActor.
// PreviewAppState is preview-only → doesn't count.
// Removing @MainActor would cause Swift 6 "crosses into main actor-isolated code" errors.

@MainActor
protocol AppStateManaging: Observable {
    var isReady: Bool { get }
    var recentProjects: [Project] { get }
    func openProject(_ url: URL)
    func clearRecentProjects()
}

@MainActor
@Observable
class AppStateManager: AppStateManaging {
    var isReady = false
    var recentProjects: [Project] = []

    func openProject(_ url: URL) { /* ... */ }
    func clearRecentProjects() { recentProjects = [] }
}

// Preview-only — doesn't affect protocol's conformer analysis
#Preview {
    struct PreviewAppState: AppStateManaging {
        var isReady = true
        var recentProjects: [Project] = []
        func openProject(_ url: URL) {}
        func clearRecentProjects() {}
    }
    // ...
}

// --- CASE 2: Per-member isolation on types with background work ---
// Protocol uses per-requirement isolation because a conformer needs background work.

protocol ProductListState: Observable {
    @MainActor var products: [Product] { get }   // View reads this
    @MainActor var isLoading: Bool { get }        // View reads this
    func fetchProducts() async                     // Network — no main needed
    func filterProducts(_ query: String) async     // Computation — no main needed
}

@Observable
class ProductListViewModel: ProductListState {
    // Only UI-driving properties are @MainActor
    @MainActor var products: [Product] = []
    @MainActor var isLoading = false

    // Fetch runs on any executor. UI update is a separate @MainActor method.
    func fetchProducts() async {
        await updateLoading(true)
        let data = try? await URLSession.shared.data(from: API.productsURL).0
        let decoded = try? JSONDecoder().decode([Product].self, from: data ?? Data())
        await updateProducts(decoded ?? [])
    }

    // Dedicated @MainActor methods for UI state mutations — clean separation
    @MainActor private func updateProducts(_ newProducts: [Product]) {
        products = newProducts
        isLoading = false
    }

    @MainActor private func updateLoading(_ loading: Bool) {
        isLoading = loading
    }

    // Pure computation — runs on whatever executor calls it
    func filterProducts(_ query: String) async {
        let filtered = products.filter { $0.name.localizedCaseInsensitiveContains(query) }
        await updateProducts(filtered)
    }
}

// --- CASE 3: No nonisolated escape hatches needed ---
// Methods are naturally free — no type-level annotation to escape from.

@Observable
class OrderViewModel {
    @MainActor var orderStatus: String = ""
    @MainActor var total: Decimal = 0

    // No @MainActor, no nonisolated — just a normal method
    func calculateTotal(items: [CartItem]) -> Decimal {
        items.reduce(0) { $0 + $1.price * Decimal($1.quantity) }
    }

    func validateOrder(_ order: Order) -> [ValidationError] {
        var errors: [ValidationError] = []
        if order.items.isEmpty { errors.append(.emptyCart) }
        if order.shippingAddress == nil { errors.append(.missingAddress) }
        return errors
    }
}
