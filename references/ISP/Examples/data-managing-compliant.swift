// ISP Compliant: Split by cohesion group with composition protocol
// DataReading: 3 methods, DataWriting: 3 methods, DataExporting: 2 methods
// All conformers 100% coverage

protocol DataReading {
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
    func search(query: String) -> [Data]
}

protocol DataWriting {
    func save(_ data: Data)
    func delete(id: String)
    func update(id: String, data: Data)
}

protocol DataExporting {
    func export(_ data: Data, format: ExportFormat) -> String
    func exportAll(format: ExportFormat) -> String
}

// Backward-compatible composition protocol
// Use protocol (not typealias) so decorators/wrappers can conform
protocol DataManaging: DataReading, DataWriting, DataExporting {}

// Full implementation — conforms to all
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

// Only conforms to what it needs — 100% coverage
final class ReadOnlyCache: DataReading {
    private var cache: [String: Data] = [:]

    func fetch(id: String) -> Data { cache[id] ?? Data() }
    func fetchAll() -> [Data] { Array(cache.values) }
    func search(query: String) -> [Data] { cache.values.filter { matches($0, query) } }
}

// Consumer narrows its dependency
final class SearchViewController {
    private let dataSource: DataReading  // only needs read access

    init(dataSource: DataReading) {
        self.dataSource = dataSource
    }

    func search(_ query: String) -> [Data] {
        dataSource.search(query: query)
    }
}
