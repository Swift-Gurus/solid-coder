extension CustomerOperations {
    func calculateTreasuryTax(_ amount: Double) -> Double {
        // Finance owns tax policy independently of customer product requirements.
        amount * 0.20
    }

    private func taxFormattingScratch() -> String { "internal" }
    fileprivate func taxStorageScratch() -> String { "internal" }
}
