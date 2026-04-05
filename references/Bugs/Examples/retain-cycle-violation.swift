// BUG-4 VIOLATION: Retain cycles, missing cleanup, swallowed errors

import Foundation

class DataSyncManager {
    var timer: Timer?
    var delegate: DataSyncDelegate? // BUG-4: should be weak — delegate pattern
    private var observers: [NSObjectProtocol] = []

    // BUG-4: retain cycle — timer captures self strongly, self holds timer
    func startAutoSync() {
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
            self.performSync()
        }
    }

    // BUG-4: retain cycle — stored closure captures self strongly
    var onSyncComplete: (() -> Void)?

    func configureSyncHandler() {
        onSyncComplete = {
            self.updateLastSyncDate() // strong capture in stored closure
            self.delegate?.syncDidComplete()
        }
    }

    // BUG-4: observer never removed — ghost callbacks after deallocation
    func observeNetworkChanges() {
        let observer = NotificationCenter.default.addObserver(
            forName: .networkStatusChanged,
            object: nil,
            queue: .main
        ) { [unowned self] _ in
            self.handleNetworkChange()
        }
        observers.append(observer)
    }

    // BUG-4: empty catch — error completely swallowed
    func performSync() {
        do {
            try syncData()
        } catch {
            // silently ignores all sync failures
        }
    }

    // BUG-4: completion handler not called on error path
    func fetchData(completion: @escaping (Result<Data, Error>) -> Void) {
        guard isNetworkAvailable else {
            return // BUG: completion never called
        }

        loadFromNetwork { result in
            completion(result)
        }
    }

    // BUG-4: print-only catch — logging is not handling
    func saveState() {
        do {
            try persistence.save(state)
        } catch {
            print("Save failed: \(error)")
        }
    }

    // Missing: deinit with timer invalidation and observer removal

    private func syncData() throws {}
    private func updateLastSyncDate() {}
    private func handleNetworkChange() {}
    private var isNetworkAvailable: Bool { true }
    private func loadFromNetwork(completion: @escaping (Result<Data, Error>) -> Void) {}
    private let persistence = Persistence()
    private var state: Data { Data() }
}

protocol DataSyncDelegate {
    func syncDidComplete()
}

extension Notification.Name {
    static let networkStatusChanged = Notification.Name("networkStatusChanged")
}

struct Persistence {
    func save(_ data: Data) throws {}
}
