/**
 solid-name: RemoteContentLoading
 solid-category: abstraction
 solid-description: Fetches one remote resource asynchronously and propagates loading failures.
 */
protocol RemoteContentLoading {
    associatedtype Content

    func loadContent() async throws -> Content
}
