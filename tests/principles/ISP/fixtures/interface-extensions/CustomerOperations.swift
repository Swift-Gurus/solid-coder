// Product requirements drive the customer-facing capabilities below.
protocol CustomerOperations {
    func renderCustomerDashboard() -> String
    func saveCustomerPreferences(_ preferences: String)
}
