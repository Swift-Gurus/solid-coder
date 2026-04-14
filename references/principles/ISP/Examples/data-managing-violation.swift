// ISP Violation: Fat protocol with 3 cohesion groups
// Group 1 (read): fetch, fetchAll, search — used by ReadOnlyCache
// Group 2 (write): save, delete, update — used by DatabaseManager
// Group 3 (export): export, exportAll — used by DatabaseManager
// ReadOnlyCache coverage: 3/8 = 37.5% → SEVERE

protocol DataManaging {
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
    func search(query: String) -> [Data]
    func save(_ data: Data)
    func delete(id: String)
    func update(id: String, data: Data)
    func export(_ data: Data, format: ExportFormat) -> String
    func exportAll(format: ExportFormat) -> String
}

// Full implementation — no ISP issue
final class DatabaseManager: DataManaging {
    func fetch(id: String) -> Data { database.read(id) }
    func fetchAll() -> [Data] { database.readAll() }
    func search(query: String) -> [Data] { database.query(query) }
    func save(_ data: Data) { database.write(data) }
    func delete(id: String) { database.remove(id) }
    func update(id: String, data: Data) { database.write(data, key: id) }
    func export(_ data: Data, format: ExportFormat) -> String { formatter.format(data, as: format) }
    func exportAll(format: ExportFormat) -> String { formatter.formatAll(database.readAll(), as: format) }
}

// ISP Violation: Only needs read operations
final class ReadOnlyCache: DataManaging {
    private var cache: [String: Data] = [:]

    func fetch(id: String) -> Data { cache[id] ?? Data() }
    func fetchAll() -> [Data] { Array(cache.values) }
    func search(query: String) -> [Data] { cache.values.filter { matches($0, query) } }

    // Forced implementations — empty/stub
    func save(_ data: Data) { }
    func delete(id: String) { }
    func update(id: String, data: Data) { }
    func export(_ data: Data, format: ExportFormat) -> String { "" }
    func exportAll(format: ExportFormat) -> String { "" }
}
