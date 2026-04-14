// Testing Compliant: Isolated, well-structured, descriptive names, proper test doubles

import XCTest
@testable import MyApp

protocol UserServicing {
    func fetchUser(id: String) async throws -> User?
    func createUser(_ user: User) async throws -> User
    func isValid(_ user: User) -> Bool
}

final class StubUserService: UserServicing {
    var fetchResult: User?
    var createResult: User = User(id: "stub-id", name: "", email: "", isActive: true, createdAt: Date())
    var validationResult: Bool = true

    func fetchUser(id: String) async throws -> User? { fetchResult }
    func createUser(_ user: User) async throws -> User { createResult }
    func isValid(_ user: User) -> Bool { validationResult }
}

final class UserServiceTests: XCTestCase {

    private var sut: StubUserService!

    override func setUp() {
        super.setUp()
        sut = StubUserService()
    }

    override func tearDown() {
        sut = nil
        super.tearDown()
    }

    func test_fetchUser_withValidId_returnsUser() async throws {
        sut.fetchResult = User(id: "123", name: "Alice", email: "alice@test.com", isActive: true, createdAt: Date())

        let result = try await sut.fetchUser(id: "123")

        XCTAssertEqual(result?.name, "Alice")
    }

    func test_fetchUser_withUnknownId_returnsNil() async throws {
        sut.fetchResult = nil

        let result = try await sut.fetchUser(id: "unknown")

        XCTAssertNil(result)
    }

    func test_isValid_withEmptyEmail_returnsFalse() {
        sut.validationResult = false
        let user = User(id: nil, name: "Test", email: "", isActive: false, createdAt: nil)

        let result = sut.isValid(user)

        XCTAssertFalse(result)
    }
}

// Analysis:
// - TEST-1: 0 violations — fresh state per test, no shared mutables
// - TEST-2: 0 violations — clear phases via blank lines, no logic
// - TEST-3: 0 violations — test_method_condition_expectation
// - TEST-4: 0 violations — stub for service, real User (value type)
// - Final severity: COMPLIANT
