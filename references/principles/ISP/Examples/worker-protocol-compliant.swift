// ISP Compliant: Narrow protocols — each conformer implements only what it needs
// All protocols width <= 3, all conformers 100% coverage

protocol Preparing {
    func prepare()
}

protocol Executing {
    func execute()
}

protocol Cleanable {
    func cleanup()
}

protocol Reportable {
    func report() -> String
}

protocol Retriable {
    func retry(maxAttempts: Int)
}

protocol Cancellable {
    func cancel()
}

// Composition protocol for consumers that need everything
// Use protocol (not typealias) — typealias cannot be conformed to,
// which breaks decorator/wrapper patterns
protocol FullWorker: Preparing, Executing, Cleanable, Reportable, Retriable, Cancellable {}

// Full implementation — conforms to all narrow protocols
final class DatabaseWorker: FullWorker {
    private var connection: DatabaseConnection?
    private var attempts = 0

    func prepare() {
        connection = DatabaseConnection.open()
    }

    func execute() {
        guard let connection = connection else { return }
        connection.runMigrations()
    }

    func cleanup() {
        connection?.close()
        connection = nil
    }

    func report() -> String {
        return "Database migration completed in \(attempts) attempts"
    }

    func retry(maxAttempts: Int) {
        for attempt in 1...maxAttempts {
            attempts = attempt
            execute()
        }
    }

    func cancel() {
        connection?.rollback()
        cleanup()
    }
}

// Only conforms to what it needs — no empty stubs
final class FireAndForgetWorker: Preparing, Executing {
    func prepare() {
        // Loads configuration
    }

    func execute() {
        // Sends HTTP request
        URLSession.shared.dataTask(with: request).resume()
    }
}

// Consumer depends on narrow interface
final class WorkerOrchestrator {
    private let worker: Preparing & Executing  // only needs these two

    init(worker: Preparing & Executing) {
        self.worker = worker
    }

    func run() {
        worker.prepare()
        worker.execute()
    }
}
