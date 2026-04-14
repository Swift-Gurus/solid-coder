// DRY-3 Violation: Embedded Infrastructure
// A generic behavioral pattern is buried inside a domain-specific type.

// 🔥 DRY-3 Violation: MessageDispatcher contains a generic queue implementation
// that is not specific to messages — any domain type could need ordered dispatch.

final class MessageDispatcher {
    private var pending: [Message] = []
    private var isProcessing = false
    private let maxRetries = 3

    func enqueue(_ message: Message) {
        pending.append(message)
        processNextIfIdle()
    }

    private func processNextIfIdle() {
        guard !isProcessing, !pending.isEmpty else { return }
        isProcessing = true
        let next = pending.removeFirst()
        process(next, attempt: 1)
    }

    private func process(_ message: Message, attempt: Int) {
        send(message) { [weak self] success in
            guard let self else { return }
            if success {
                self.isProcessing = false
                self.processNextIfIdle()
            } else if attempt < self.maxRetries {
                self.process(message, attempt: attempt + 1)
            } else {
                self.isProcessing = false
                self.processNextIfIdle()
            }
        }
    }

    private func send(_ message: Message, completion: @escaping (Bool) -> Void) {
        // domain-specific: send message over network
    }
}

// Analysis:
// - Domain: message dispatching
// - Embedded pattern: serial queue with retry (enqueue → process one at a time → retry on failure)
// - Reuse potential: YES — any domain type needing ordered processing with retry
//   (event dispatching, task scheduling, notification delivery) would need the same pattern
// - Embedded infrastructure: 1 → SEVERE
