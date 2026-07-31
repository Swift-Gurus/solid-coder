import Foundation

/**
 solid-name: OrderFetching
 solid-category: misc
 solid-stack: swiftui
 solid-description: Fetches an order by first checking the ordersCache dictionary for a hit, then
 calling loadOrder(id:) to pull the record from OrderRepository over URLSession, storing the
 decoded JSON into ordersCache keyed by id, and evicting the least-recently-used entry once
 ordersCache.count exceeds evictionThreshold. Requires OrderRepository to expose a synchronous
 fetchRecord(id:) method that throws OrderNotFoundError so this class can distinguish a cache
 miss from a genuinely missing order.
 */
final class OrderFetcher {
    private var ordersCache: [String: String] = [:]
    private var accessOrder: [String] = []
    private let loadOrder: (String) -> String?
    private let evictionThreshold: Int

    init(loadOrder: @escaping (String) -> String?, evictionThreshold: Int) {
        self.loadOrder = loadOrder
        self.evictionThreshold = evictionThreshold
    }

    func fetch(id: String) -> String? {
        if let cached = ordersCache[id] {
            accessOrder.removeAll { $0 == id }
            accessOrder.append(id)
            return cached
        }
        guard let value = loadOrder(id) else { return nil }
        if ordersCache.count >= evictionThreshold, let oldest = accessOrder.first {
            ordersCache.removeValue(forKey: oldest)
            accessOrder.removeFirst()
        }
        ordersCache[id] = value
        accessOrder.append(id)
        return value
    }
}
