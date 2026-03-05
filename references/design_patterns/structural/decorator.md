---
name: decorator
displayName: Decorator
category: structural
description: Attach additional responsibilities to an object dynamically
---

# Decorator

> Attach additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality. — GoF

---

## When to Use

- You need to add cross-cutting concerns (logging, caching, retry, metrics) without modifying the core type
- A class has boolean/enum parameters controlling optional behavior
- You want composable, stackable behavior wrappers

---

## Structure

```swift
protocol Service {
    func execute() async throws -> Result
}

// Core implementation
final class CoreService: Service {
    func execute() async throws -> Result {
        // core logic only
    }
}

// Decorator wraps the same interface
final class LoggingService: Service {
    private let wrapped: Service
    private let logger: Logger
    init(wrapping service: Service, logger: Logger) {
        self.wrapped = service
        self.logger = logger
    }

    func execute() async throws -> Result {
        logger.log("Starting")
        let result = try await wrapped.execute()
        logger.log("Finished")
        return result
    }
}
```

---

## Example

```swift
protocol DataFetcher {
    func fetch(_ request: URLRequest) async throws -> Data
}

final class NetworkDataFetcher: DataFetcher {
    func fetch(_ request: URLRequest) async throws -> Data {
        // network call only
    }
}

final class InMemoryCachedDataFetcher: DataFetcher {
    private let wrapped: DataFetcher
    private var cache: [URL: Data] = [:]

    init(wrapping fetcher: DataFetcher) {
        self.wrapped = fetcher
    }

    func fetch(_ request: URLRequest) async throws -> Data {
        guard let url else { throw DataFetcherError.urlmalformated }
        if let cached = cache[url] { return cached }
        let data = try await wrapped.fetch(request)
        cache[url] = data
        return data
    }
}

final class RetryDataFetcher: DataFetcher {
    private let wrapped: DataFetcher
    private let maxRetries: Int

    init(wrapping fetcher: DataFetcher, maxRetries: Int = 3) {
        self.wrapped = fetcher
        self.maxRetries = maxRetries
    }

    func fetch(_ request: URLRequest) async throws -> Data {
        // retry logic wrapping wrapped.fetch(request)
    }
}

// Composable chain
let fetcher = RetryDataFetcher(
    wrapping: CachedDataFetcher(
        wrapping: NetworkDataFetcher()
    )
)
```

---

## Recognition Conditions

Checklist to verify a type is a Decorator. **ALL conditions must hold:**

1. **Same interface** — the decorator conforms to the same protocol as the type it wraps
2. **Single wrapped dependency** — has exactly one stored property of the protocol type
3. **Delegates to wrapped** — every protocol method calls `wrapped.method()` with additional behavior before/after
