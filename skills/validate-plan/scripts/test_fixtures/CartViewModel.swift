// solid-category: viewmodel
// solid-description: Manages cart state and handles checkout flow

import SwiftUI

@Observable
final class CartViewModel {
    var items: [CartItem] = []

    func checkout() async throws {}
}
