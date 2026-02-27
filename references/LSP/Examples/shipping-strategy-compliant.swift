// LSP-2 Compliant: All subtypes honor base contract
// - WorldWideShipping: handles nil destination instead of rejecting
// - FreeShipping: returns minimum positive value, honoring postcondition
// - ExpressShipping: routes through validated setter

enum ShippingError: Error {
    case invalidWeight
    case invalidResult(String)
    case invalidFlatRate
}

enum Region {
    case domestic
    case international
    case unknown
}

class ShippingStrategy {
    private var _flatRate: Decimal

    var flatRate: Decimal {
        get { _flatRate }
    }

    init(flatRate: Decimal) throws {
        guard flatRate > 0 else {
            throw ShippingError.invalidFlatRate
        }
        self._flatRate = flatRate
    }

    func setFlatRate(_ newRate: Decimal) throws {
        guard newRate > 0 else {
            throw ShippingError.invalidFlatRate
        }
        _flatRate = newRate
    }

    // Contract:
    // - Precondition: weight > 0, destination can be nil
    // - Postcondition: returned cost > 0
    func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }

        let cost = Decimal(Double(weight)) * _flatRate
        guard cost > 0 else {
            throw ShippingError.invalidResult("Cost must be positive")
        }
        return cost
    }
}

// Compliant: handles nil destination (same or weaker precondition)
class WorldWideShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        let region = destination ?? .unknown  // Handle nil, don't reject
        let multiplier: Decimal = region == .international ? 2 : 1
        let cost = Decimal(Double(weight)) * flatRate * multiplier
        guard cost > 0 else {
            throw ShippingError.invalidResult("Cost must be positive")
        }
        return cost
    }
}

// Compliant: returns minimum positive value (honors postcondition cost > 0)
class FreeShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        if destination == .domestic {
            return 0.01  // Minimum positive — honors postcondition
        }
        return try super.calculateCost(weight: weight, destination: destination)
    }
}

// Compliant: routes through validated setter (preserves invariant)
class ExpressShipping: ShippingStrategy {
    func updateFlatRate(_ newRate: Decimal) throws {
        try setFlatRate(newRate)  // Uses base validation — invariant preserved
    }
}

// Client code works correctly with ALL subtypes
func processShipment(strategy: ShippingStrategy) throws {
    let cost = try strategy.calculateCost(weight: 5.0, destination: nil)
    let percentage = 1.0 / Double(truncating: cost as NSNumber)  // Safe: cost > 0
    print("Cost: \(cost), percentage: \(percentage)")
}
