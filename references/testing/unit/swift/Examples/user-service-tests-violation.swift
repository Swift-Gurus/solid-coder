// Testing Violations: Isolation, Structure, Naming, Test Double Quality
// Multiple violations across all four metrics.

import XCTest
@testable import MyApp

// TEST-1 VIOLATION: Shared mutable state — static var persists across tests
// TEST-4 VIOLATION: No protocol boundary for UserService — can't inject test double
class UserServiceTests: XCTestCase {

    static var lastCreatedUser: User?  // ❌ TEST-1: Shared mutable state across tests
    var service: UserService!

    override func setUp() {
        super.setUp()
        // ❌ TEST-1: Real network dependency — UserService internally uses URLSession.shared
        service = UserService()
    }

    // ❌ TEST-3: Non-descriptive name — what scenario? what expectation?
    func testFetch() async throws {
        // ❌ TEST-1: Real network call — hits actual API
        let user = try await service.fetchUser(id: "123")
        XCTAssertNotNil(user)
    }

    // ❌ TEST-3: Missing condition and expectation
    func testCreate() async throws {
        let user = User(name: "Alice", email: "alice@test.com")
        let created = try await service.createUser(user)

        // ❌ TEST-1: Writes to shared static — next test depends on this
        UserServiceTests.lastCreatedUser = created

        // ❌ TEST-2: Multiple unrelated behaviors in one test
        XCTAssertNotNil(created.id)
        XCTAssertEqual(created.name, "Alice")
        XCTAssertEqual(created.email, "alice@test.com")
        XCTAssertTrue(created.isActive)
        XCTAssertNotNil(created.createdAt)

        // ❌ TEST-2: Second action in the same test — fetching after creating
        let fetched = try await service.fetchUser(id: created.id!)
        XCTAssertEqual(fetched?.name, "Alice")
    }

    // ❌ TEST-1: Depends on testCreate running first (reads shared static)
    // ❌ TEST-3: Name doesn't describe the scenario
    func testDelete() async throws {
        // ❌ TEST-1: Test interdependency — assumes testCreate populated lastCreatedUser
        guard let user = UserServiceTests.lastCreatedUser else {
            XCTFail("No user created in previous test")
            return
        }

        try await service.deleteUser(id: user.id!)

        // ❌ TEST-2: Logic in test — conditional assertion
        if let fetched = try? await service.fetchUser(id: user.id!) {
            XCTFail("User should have been deleted but found: \(fetched)")
        }
    }

    // ❌ TEST-3: Generic name with no specificity
    func testValidation() {
        // ❌ TEST-2: Loop in test — should be parameterized or separate tests
        let invalidEmails = ["", "notanemail", "@missing.com", "no@"]
        for email in invalidEmails {
            let user = User(name: "Test", email: email)
            XCTAssertFalse(service.isValid(user), "Expected \(email) to be invalid")
        }
    }

    // ❌ TEST-4: Over-mocking — mocking a simple value type
    func testUserEquality() {
        let mockUser1 = MockUser(name: "Alice", email: "a@b.com")  // ❌ Why mock a value type?
        let mockUser2 = MockUser(name: "Alice", email: "a@b.com")
        XCTAssertEqual(mockUser1, mockUser2)
    }
}

// ❌ TEST-4: Unnecessary mock — User is a value type, use real instance
class MockUser: Equatable {
    let name: String
    let email: String
    init(name: String, email: String) { self.name = name; self.email = email }
    static func == (lhs: MockUser, rhs: MockUser) -> Bool {
        lhs.name == rhs.name && lhs.email == rhs.email
    }
}

// Analysis:
// - TEST-1 isolation violations: 4 (shared static, real network x2, test interdependency)
// - TEST-2 structure violations: 3 (multiple behaviors, logic in test, loop in test)
// - TEST-3 naming violations: 4 (testFetch, testCreate, testDelete, testValidation — all non-descriptive)
// - TEST-4 test double violations: 2 (no protocol for UserService, MockUser for value type)
// - Final severity: SEVERE
