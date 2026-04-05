---
name: bugs
displayName: Bug Patterns
category: practice
description: Patterns and examples for fixing common bug patterns in Swift
---
# Bug Patterns

> Bugs hide in patterns. Detect the pattern, prevent the crash.
---

## Bug Fix Approaches

This document provides before/after examples for each bug fix category.

---

## BUG-1 Fixes: Unsafe Unwrap and Access

### Guard Clause — Replace Force Unwrap

```swift
// BEFORE: force unwrap crashes if nil
func loadUser() -> User {
    let data = fetchUserData()!
    let user = JSONDecoder().decode(User.self, from: data)
    return user
}

// AFTER: guard clause with meaningful error
func loadUser() throws -> User {
    guard let data = fetchUserData() else {
        throw UserError.dataNotFound
    }
    let user = try JSONDecoder().decode(User.self, from: data)
    return user
}
```

### Optional Binding — Replace Force Cast

```swift
// BEFORE: force cast crashes on type mismatch
let response = urlResponse as! HTTPURLResponse

// AFTER: optional binding with handling
guard let response = urlResponse as? HTTPURLResponse else {
    throw NetworkError.invalidResponse
}
```

### Safe Subscript — Replace Unguarded Array Access

```swift
// BEFORE: crashes if index out of bounds
let item = items[selectedIndex]

// AFTER: guarded access
guard items.indices.contains(selectedIndex) else {
    return nil
}
let item = items[selectedIndex]
```

### Nil Coalescing — Replace Dictionary Force Unwrap

```swift
// BEFORE: crashes if key missing
let name = userInfo["name"]!

// AFTER: nil coalescing with default
let name = userInfo["name"] ?? "Unknown"
```

---

## BUG-2 Fixes: Logic and Semantic Bugs

### Remove Dead Code

```swift
// BEFORE: unreachable code after return
func validate(_ input: String) -> Bool {
    guard !input.isEmpty else { return false }
    return input.count > 3
    print("Validation complete") // unreachable
}

// AFTER: dead code removed
func validate(_ input: String) -> Bool {
    guard !input.isEmpty else { return false }
    return input.count > 3
}
```

### Add Missing Switch Cases

```swift
// BEFORE: empty default hides future enum cases
enum PaymentStatus {
    case pending, processing, completed, failed, refunded
}

func handle(_ status: PaymentStatus) {
    switch status {
    case .completed: markComplete()
    case .failed: retry()
    default: break // silently ignores pending, processing, refunded
    }
}

// AFTER: explicit handling for every case
func handle(_ status: PaymentStatus) {
    switch status {
    case .pending: showPendingUI()
    case .processing: showProgressUI()
    case .completed: markComplete()
    case .failed: retry()
    case .refunded: showRefundConfirmation()
    }
}
```

### Fix Contradictory Conditions

```swift
// BEFORE: impossible condition
func filterItems(_ items: [Item], minPrice: Double, maxPrice: Double) -> [Item] {
    // Bug: minPrice=100, maxPrice=50 returns nothing — no validation
    return items.filter { $0.price >= minPrice && $0.price <= maxPrice }
}

// AFTER: precondition catches invalid arguments
func filterItems(_ items: [Item], minPrice: Double, maxPrice: Double) -> [Item] {
    precondition(minPrice <= maxPrice, "minPrice must be <= maxPrice")
    return items.filter { $0.price >= minPrice && $0.price <= maxPrice }
}
```

---

## BUG-3 Fixes: Concurrency Bugs

### Actor Isolation — Protect Shared Mutable State

```swift
// BEFORE: data race on shared cache
class ImageCache {
    static var shared = ImageCache()
    private var cache: [URL: Data] = [:] // mutable, no synchronization

    func store(_ data: Data, for url: URL) {
        cache[url] = data // race condition
    }

    func retrieve(for url: URL) -> Data? {
        cache[url] // race condition
    }
}

// AFTER: actor eliminates data races
actor ImageCache {
    static let shared = ImageCache()
    private var cache: [URL: Data] = [:]

    func store(_ data: Data, for url: URL) {
        cache[url] = data // actor-isolated, safe
    }

    func retrieve(for url: URL) -> Data? {
        cache[url] // actor-isolated, safe
    }
}
```

### Dispatch to Background — Fix Main-Thread Blocking

```swift
// BEFORE: synchronous I/O on main thread
func loadConfig() -> Config {
    let data = try! Data(contentsOf: configURL) // blocks main thread
    return try! JSONDecoder().decode(Config.self, from: data)
}

// AFTER: async loading off main thread
func loadConfig() async throws -> Config {
    let data = try await Task.detached {
        try Data(contentsOf: configURL)
    }.value
    return try JSONDecoder().decode(Config.self, from: data)
}
```

### Fix Deadlock Risk

```swift
// BEFORE: potential deadlock — sync on main from main
func updateUI(with data: Data) {
    DispatchQueue.main.sync { // deadlock if already on main
        self.label.text = String(data: data, encoding: .utf8)
    }
}

// AFTER: async dispatch avoids deadlock
func updateUI(with data: Data) {
    DispatchQueue.main.async {
        self.label.text = String(data: data, encoding: .utf8)
    }
}
```

---

## BUG-4 Fixes: Safety and Correctness

### Weak Capture — Fix Retain Cycle

```swift
// BEFORE: retain cycle — timer holds self, self holds timer
class PollingService {
    var timer: Timer?

    func startPolling() {
        timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            self.fetchUpdates() // strong capture of self
        }
    }
}

// AFTER: weak capture breaks the cycle
class PollingService {
    var timer: Timer?

    func startPolling() {
        timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            self?.fetchUpdates()
        }
    }

    deinit {
        timer?.invalidate()
    }
}
```

### Resource Cleanup — NotificationCenter Observer

```swift
// BEFORE: observer never removed — leaks and ghost callbacks
class ProfileViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        NotificationCenter.default.addObserver(
            self, selector: #selector(refresh), name: .userUpdated, object: nil
        )
    }
    // Missing: removeObserver in deinit
}

// AFTER: cleanup in deinit
class ProfileViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        NotificationCenter.default.addObserver(
            self, selector: #selector(refresh), name: .userUpdated, object: nil
        )
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
```

### Error Propagation — Replace Empty Catch

```swift
// BEFORE: error swallowed — failures are invisible
func saveProfile(_ profile: Profile) {
    do {
        try persistence.save(profile)
    } catch {
        print(error) // logging is not handling
    }
}

// AFTER: error propagated to caller
func saveProfile(_ profile: Profile) throws {
    do {
        try persistence.save(profile)
    } catch {
        logger.error("Failed to save profile: \(error)")
        throw ProfileError.saveFailed(underlying: error)
    }
}
```

### Completion Handler on All Paths

```swift
// BEFORE: completion not called on error path
func fetchUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
    guard !id.isEmpty else {
        return // BUG: completion never called
    }
    api.get("/users/\(id)") { result in
        completion(result)
    }
}

// AFTER: completion called on every path
func fetchUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
    guard !id.isEmpty else {
        completion(.failure(UserError.invalidID))
        return
    }
    api.get("/users/\(id)") { result in
        completion(result)
    }
}
```

### Float Equality — Epsilon Comparison

```swift
// BEFORE: floating point equality is unreliable
func isBalanced(_ a: Double, _ b: Double) -> Bool {
    return a == b // 0.1 + 0.2 != 0.3
}

// AFTER: epsilon comparison
func isBalanced(_ a: Double, _ b: Double, epsilon: Double = 1e-10) -> Bool {
    return abs(a - b) < epsilon
}
```
