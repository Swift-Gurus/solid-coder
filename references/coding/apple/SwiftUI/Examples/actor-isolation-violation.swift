// SUI-9 VIOLATION: Type-level @MainActor on ViewModel with background-safe members
// The entire class is forced onto main thread, preventing background work.

import SwiftUI

// VIOLATION 1: Protocol-level @MainActor — but only because a production conformer
// (BackgroundProductLoader) needs to run fetchProducts() off main.
// If ALL conformers were @MainActor, this would be COMPLIANT.
@MainActor
protocol ProductListState: Observable {
    var products: [Product] { get }
    var isLoading: Bool { get }
    func fetchProducts() async        // BackgroundProductLoader needs this off main
    func filterProducts(_ query: String)
}

// Production conformer that is @MainActor — fine on its own
@MainActor
@Observable
class ProductListViewModel: ProductListState {
    var products: [Product] = []
    var isLoading = false

    func fetchProducts() async {
        isLoading = true
        let data = try? await URLSession.shared.data(from: API.productsURL).0
        let decoded = try? JSONDecoder().decode([Product].self, from: data ?? Data())
        products = decoded ?? []
        isLoading = false
    }

    func filterProducts(_ query: String) {
        products = products.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }
}

// Production conformer that needs background work — THIS is why the protocol is a violation.
// The @MainActor protocol forces fetchProducts() onto main even though this type
// is designed to run it in the background.
@MainActor // forced by protocol
@Observable
class BackgroundProductLoader: ProductListState {
    var products: [Product] = []
    var isLoading = false

    // This SHOULD run on a background thread, but the protocol forces it onto main
    func fetchProducts() async {
        isLoading = true
        // Heavy batch processing that blocks main thread
        let data = try? await URLSession.shared.data(from: API.productsURL).0
        let decoded = try? JSONDecoder().decode([Product].self, from: data ?? Data())
        let processed = decoded?.map { expensiveTransform($0) } ?? []
        products = processed
        isLoading = false
    }

    func filterProducts(_ query: String) {
        products = products.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }
}

// VIOLATION 2: Type-level @MainActor on VM with background-safe methods
@MainActor
@Observable
class OrderViewModel {
    var orderStatus: String = ""
    var total: Decimal = 0

    // This method does network I/O + JSON parsing, all forced onto main thread.
    func placeOrder(_ order: Order) async {
        orderStatus = "placing"
        let result = try? await APIClient.shared.post(order)
        orderStatus = result?.status ?? "failed"
    }

    // Pure computation forced onto main thread
    func calculateTotal(items: [CartItem]) -> Decimal {
        items.reduce(0) { $0 + $1.price * Decimal($1.quantity) }
    }
}

// VIOLATION 3: nonisolated escape hatch — a smell that @MainActor is too broad
@MainActor
@Observable
class CheckoutViewModel {
    var validationErrors: [ValidationError] = []
    var isValid = false

    // Developer already knows this shouldn't be on main — the nonisolated proves it
    nonisolated func validateOrder(_ order: Order) -> [ValidationError] {
        var errors: [ValidationError] = []
        if order.items.isEmpty { errors.append(.emptyCart) }
        if order.shippingAddress == nil { errors.append(.missingAddress) }
        return errors
    }

    nonisolated func formatReceipt(_ order: Order) -> String {
        // Complex string formatting forced off main via escape hatch
        order.items.map { "\($0.name): \($0.price)" }.joined(separator: "\n")
    }
}
