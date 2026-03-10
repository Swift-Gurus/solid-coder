// ISP Violation: Wide protocol forces conformers to implement unused methods
// Protocol width: 6, FireAndForgetWorker coverage: 33% (2/6 meaningful)

protocol Worker {
    func prepare()
    func execute()
    func cleanup()
    func report() -> String
    func retry(maxAttempts: Int)
    func cancel()
}

// Full implementation — 100% coverage, no ISP issue for this conformer
final class DatabaseWorker: Worker {
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

// ISP Violation: Only needs execute() and prepare()
// 2/6 meaningful = 33% coverage → SEVERE
final class FireAndForgetWorker: Worker {
    func prepare() {
        // Loads configuration — meaningful
    }

    func execute() {
        // Sends HTTP request — meaningful
        URLSession.shared.dataTask(with: request).resume()
    }

    func cleanup() { }                          // empty — not needed
    func report() -> String { return "" }        // stub — never reports
    func retry(maxAttempts: Int) { }               // empty — ignores retry semantics
    func cancel() { }                            // empty — fire and forget
}
