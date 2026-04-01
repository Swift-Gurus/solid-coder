// TEST-2 Compliant: Deterministic async waiting
// Test doubles own expectations — coordinator wires them on creation.

import XCTest
@testable import MyApp

final class DataPipelineTests: XCTestCase {

    private var coordinator: DataPipelineTestCoordinator!

    override func setUp() {
        super.setUp()
        coordinator = DataPipelineTestCoordinator()
    }

    override func tearDown() {
        coordinator = nil
        super.tearDown()
    }

    private var sut: DataPipeline { coordinator.makeSUT() }

    func test_pipeline_processesAllStages() async {
        let sut = self.sut

        sut.run()

        await waitForAllExpectations()

        XCTAssertTrue(coordinator.mockFetcher.didFetch)
        XCTAssertTrue(coordinator.mockTransformer.didTransform)
        XCTAssertTrue(coordinator.mockPersister.didPersist)
    }

    func test_pipeline_fetchesMultiplePages() async {
        coordinator.mockFetcher.expectedFulfillmentCount = 3
        coordinator.resetExpectations()
        let sut = self.sut

        sut.fetchAll(pages: 3)

        await waitForAllExpectations()

        XCTAssertEqual(coordinator.mockFetcher.fetchCount, 3)
    }

    private func waitForAllExpectations(timeout: TimeInterval = 5.0) async {
        await fulfillment(of: coordinator.expectations, timeout: timeout, enforceOrder: true)
    }
}

private final class MockFetcher: Fetching {
    var didFetch = false
    var fetchCount = 0
    var expectedFulfillmentCount = 1
    var expectation: XCTestExpectation?

    func fetch() async {
        didFetch = true
        fetchCount += 1
        expectation?.fulfill()
    }
}

private final class MockTransformer: Transforming {
    var didTransform = false
    var expectation: XCTestExpectation?

    func transform() async {
        didTransform = true
        expectation?.fulfill()
    }
}

private final class MockPersister: Persisting {
    var didPersist = false
    var expectation: XCTestExpectation?

    func persist() async {
        didPersist = true
        expectation?.fulfill()
    }
}

private final class DataPipelineTestCoordinator {

    let mockFetcher = MockFetcher()
    let mockTransformer = MockTransformer()
    let mockPersister = MockPersister()

    var expectations: [XCTestExpectation] {
        [mockFetcher.expectation, mockTransformer.expectation, mockPersister.expectation]
            .compactMap { $0 }
    }

    func makeSUT() -> DataPipeline {
        prepareExpectations()

        return DataPipeline(
            fetcher: mockFetcher,
            transformer: mockTransformer,
            persister: mockPersister
        )
    }

    func resetExpectations() {
        prepareExpectations()
    }

    private func prepareExpectations() {
        let fetchExp = XCTestExpectation(description: "fetch")
        fetchExp.expectedFulfillmentCount = mockFetcher.expectedFulfillmentCount
        mockFetcher.expectation = fetchExp

        mockTransformer.expectation = XCTestExpectation(description: "transform")
        mockPersister.expectation = XCTestExpectation(description: "persist")
    }
}

// Analysis:
// - No sleep calls — mocks own expectations, fulfill when SUT calls them
// - prepareExpectations() is the single source of expectation creation
// - makeSUT() calls prepareExpectations() then returns wired SUT
// - resetExpectations() recreates them (e.g., after changing expectedFulfillmentCount)
// - `let sut = self.sut` captures once per test
// - coordinator.expectations collects non-nil expectations from all mocks
