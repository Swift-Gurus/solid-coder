import Foundation

class OrderRepository {
    private let store: UserDefaults

    init(store: UserDefaults) {
        self.store = store
    }

    func save(_ order: Data, id: String) {
        store.set(order, forKey: id)
    }

    func load(id: String) -> Data? {
        store.data(forKey: id)
    }

    func remove(id: String) {
        store.removeObject(forKey: id)
    }

    func exists(id: String) -> Bool {
        store.data(forKey: id) != nil
    }
}
