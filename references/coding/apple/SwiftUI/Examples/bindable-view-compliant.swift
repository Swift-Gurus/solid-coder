// COMPLIANT: View uses @Bindable with protocol-constrained generic for two-way bindings
// SUI-4: VM injected via protocol generic → COMPLIANT
// Key: @Bindable works with protocol-constrained generics because Observable conformance is guaranteed

protocol SettingsState: Observable {
    var name: String { get set }
    var notificationsEnabled: Bool { get set }
}

protocol SettingsActions {
    func save()
}

struct SettingsView<VM: SettingsState & SettingsActions>: View {
    var vm: VM

    var body: some View {
        @Bindable var bindable = vm  // local @Bindable wraps the generic
        Form {
            TextField("Name", text: $bindable.name)
            Toggle("Notifications", isOn: $bindable.notificationsEnabled)
            Button("Save") { vm.save() }
        }
    }
}

// MARK: - ViewModel conforms to both protocols

@Observable
final class SettingsViewModel: SettingsState, SettingsActions {
    var name: String = ""
    var notificationsEnabled: Bool = true

    func save() { /* ... */ }
}
