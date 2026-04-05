// BUG-4 COMPLIANT: Weak captures, proper cleanup, error propagation

import Foundation

class DataSyncManager {
    var timer: Timer?
    weak var delegate: DataSyncDelegate? // weak delegate breaks retain cycle
    private var observers: [NSObjectProtocol] = []

    // Safe: [weak self] breaks timer retain cycle
    func startAutoSync() {
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            self?.performSync()
        }
    }

    // Safe: [weak self] in stored closure
    var onSyncComplete: (() -> Void)?

    func configureSyncHandler() {
        onSyncComplete = { [weak self] in
            self?.updateLastSyncDate()
            self?.delegate?.syncDidComplete()
        }
    }

    // Safe: observers tracked and removed in deinit
    func observeNetworkChanges() {
        let observer = NotificationCenter.default.addObserver(
            forName: .networkStatusChanged,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.handleNetworkChange()
        }
        observers.append(observer)
    }

    // Safe: error logged and propagated
    func performSync() {
        do {
            try syncData()
        } catch {
            logger.error("Sync failed: \(error)")
            delegate?.syncDidFail(with: error)
        }
    }

    // Safe: completion called on ALL paths
    func fetchData(completion: @escaping (Result<Data, Error>) -> Void) {
        guard isNetworkAvailable else {
            completion(.failure(SyncError.networkUnavailable))
            return
        }

        loadFromNetwork { result in
            completion(result)
        }
    }

    // Safe: error propagated to caller
    func saveState() throws {
        do {
            try persistence.save(state)
        } catch {
            logger.error("Save failed: \(error)")
            throw SyncError.saveFailed(underlying: error)
        }
    }

    // Proper cleanup in deinit
    deinit {
        timer?.invalidate()
        observers.forEach { NotificationCenter.default.removeObserver($0) }
    }

    private func syncData() throws {}
    private func updateLastSyncDate() {}
    private func handleNetworkChange() {}
    private var isNetworkAvailable: Bool { true }
    private func loadFromNetwork(completion: @escaping (Result<Data, Error>) -> Void) {}
    private let persistence = Persistence()
    private var state: Data { Data() }
    private let logger = Logger()
}

protocol DataSyncDelegate: AnyObject {
    func syncDidComplete()
    func syncDidFail(with error: Error)
}

enum SyncError: Error {
    case networkUnavailable
    case saveFailed(underlying: Error)
}

extension Notification.Name {
    static let networkStatusChanged = Notification.Name("networkStatusChanged")
}

struct Persistence {
    func save(_ data: Data) throws {}
}

struct Logger {
    func error(_ message: String) {}
}
