// LSP-2 Violation: Contract compliance failures in class hierarchy
// - WorldWideShipping: strengthened precondition (new guard)
// - FreeShipping: weakened postcondition (returns 0, base guarantees > 0)
// - ExpressShipping: broken invariant (exposed unguarded setter)

enum ShippingError: Error {
    case invalidWeight
    case invalidResult(String)
    case invalidFlatRate
    case destinationRequired
}

enum Region {
    case domestic
    case international
    case unknown
}

// Base class: defines the contract
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

// LSP-2 Violation: Strengthened precondition
// Base allows destination == nil, subtype REQUIRES it
class WorldWideShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        guard let destination = destination else {          // NEW guard — violation!
            throw ShippingError.destinationRequired         // Base never throws this
        }
        return Decimal(Double(weight)) * flatRate * 2
    }
}

// LSP-2 Violation: Weakened postcondition
// Base guarantees cost > 0, subtype returns 0
class FreeShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        if destination == .domestic {
            return 0    // Violates postcondition: cost > 0
        }
        return try super.calculateCost(weight: weight, destination: destination)
    }
}

// LSP-2 Violation: Broken invariant
// Base protects flatRate > 0 via validated setter, subtype exposes unguarded setter
class ExpressShipping: ShippingStrategy {
    override var flatRate: Decimal {
        get { super.flatRate }
        set { /* _flatRate = newValue — bypasses validation, can set negative */ }
    }
}

// Client code that breaks when substituting subtypes
func processShipment(strategy: ShippingStrategy) throws {
    // Works with base ShippingStrategy
    // Breaks with WorldWideShipping when destination is nil
    let cost = try strategy.calculateCost(weight: 5.0, destination: nil)

    // Works with base ShippingStrategy (cost > 0 guaranteed)
    // Breaks with FreeShipping (division by zero)
    let percentage = 1.0 / Double(truncating: cost as NSNumber)

    print("Cost: \(cost), percentage: \(percentage)")
}
