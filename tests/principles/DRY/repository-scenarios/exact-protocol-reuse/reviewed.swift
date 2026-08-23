/**
 solid-name: NetworkResourceFetching
 solid-category: abstraction
 solid-description: Retrieves one remote resource asynchronously and propagates loading failures.
 */
protocol NetworkResourceFetching {
    associatedtype Resource

    func fetchResource() async throws -> Resource
}
