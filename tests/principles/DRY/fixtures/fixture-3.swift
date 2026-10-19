import Foundation

struct PayrollLedger {
    struct Entry {
        let hours: Double
        let rate: Double
        let category: String
    }

    func grossWages(_ entries: [Entry]) -> Double {
        var subtotal = 0.0
        for entry in entries {
            guard entry.hours > 0 else { continue }
            guard entry.rate > 0 else { continue }
            let weighted = entry.hours * entry.rate
            subtotal += weighted
        }
        return (subtotal * 100).rounded() / 100
    }

    func reimbursements(_ entries: [Entry]) -> Double {
        var subtotal = 0.0
        for entry in entries {
            guard entry.hours > 0 else { continue }
            guard entry.rate > 0 else { continue }
            let weighted = entry.hours * entry.rate
            subtotal += weighted
        }
        return (subtotal * 10).rounded() / 10
    }
}
