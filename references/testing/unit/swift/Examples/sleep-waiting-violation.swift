// TEST-2 Violation: Sleep-based waiting for async operations
// Flaky, slow, and masks real timing issues.

import XCTest
@testable import MyApp

final class DataPipelineTests: XCTestCase {

    func test_pipeline_processesInOrder() async throws {
        let sut = DataPipeline(fetcher: mockFetcher, transformer: mockTransformer, persister: mockPersister)

        sut.run()

        try await Task.sleep(nanoseconds: 500_000_000)
        XCTAssertTrue(mockFetcher.didFetch)

        try await Task.sleep(nanoseconds: 500_000_000)
        XCTAssertTrue(mockTransformer.didTransform)

        try await Task.sleep(nanoseconds: 500_000_000)
        XCTAssertTrue(mockPersister.didPersist)
    }
}

// Analysis:
// - Chained sleeps to wait for dependent async operations
// - Hardcoded delays: too short = flaky, too long = slow suite
// - No deterministic signal that work is actually done
