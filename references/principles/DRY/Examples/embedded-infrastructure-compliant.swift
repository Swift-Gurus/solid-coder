// DRY-3 Compliant: Abstraction extracted
// The serial queue is a standalone reusable type. Retry is a decorator on top.

// ✅ Compliant: generic queue extracted as standalone type

protocol SerialQueuing<T> {
    associatedtype T
    func enqueue(_ item: T)
}

final class SerialQueue<T>: SerialQueuing {
    private var pending: [T] = []
    private var isProcessing = false
    private let operation: (T, @escaping (Bool) -> Void) -> Void

    init(operation: @escaping (T, @escaping (Bool) -> Void) -> Void) {
        self.operation = operation
    }

    func enqueue(_ item: T) {
        pending.append(item)
        processNextIfIdle()
    }

    private func processNextIfIdle() {
        guard !isProcessing, !pending.isEmpty else { return }
        isProcessing = true
        let next = pending.removeFirst()
        operation(next) { [weak self] _ in
            self?.isProcessing = false
            self?.processNextIfIdle()
        }
    }
}

// ✅ Retry is a decorator — separate concern, reusable on any queue

final class RetryingQueue<Decorated: SerialQueuing>: SerialQueuing {
    typealias T = Decorated.T

    private let decorated: Decorated
    private let maxRetries: Int
    private let operation: (T, @escaping (Bool) -> Void) -> Void

    init(decorating queue: Decorated, maxRetries: Int, operation: @escaping (T, @escaping (Bool) -> Void) -> Void) {
        self.decorated = queue
        self.maxRetries = maxRetries
        self.operation = operation
    }

    func enqueue(_ item: T) {
        attempt(item, remaining: maxRetries)
    }

    private func attempt(_ item: T, remaining: Int) {
        operation(item) { [weak self] success in
            guard let self else { return }
            if success || remaining <= 1 {
                self.decorated.enqueue(item)
            } else {
                self.attempt(item, remaining: remaining - 1)
            }
        }
    }
}

// Domain type is generic over the queue — injectable, testable

protocol MessageDispatching {
    func dispatch(_ message: Message)
}

final class MessageDispatcher<Q: SerialQueuing>: MessageDispatching where Q.T == Message {
    private let queue: Q

    init(queue: Q) {
        self.queue = queue
    }

    func dispatch(_ message: Q.T) {
        queue.enqueue(message)
    }
}

// Analysis:
// - SerialQueue is generic — reusable for any domain type
// - RetryingQueue is a decorator — adds retry without modifying the queue (OCP compliant)
// - MessageDispatcher is generic over Q: SerialQueuing where Q.T == Message (OCP compliant)
// - Queue injected via init (OCP compliant)
// - Missing abstractions: 0 → COMPLIANT
