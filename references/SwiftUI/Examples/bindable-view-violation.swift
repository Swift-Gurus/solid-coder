// VIOLATION: View uses @Bindable with concrete ViewModel type
// SUI-4: Concrete VM injection → SEVERE

@Observable
final class SettingsViewModel {
    var name: String = ""
    var notificationsEnabled: Bool = true

    func save() { /* ... */ }
}

struct SettingsView: View {
    @Bindable var vm: SettingsViewModel  // VIOLATION: concrete type

    var body: some View {
        Form {
            TextField("Name", text: $vm.name)
            Toggle("Notifications", isOn: $vm.notificationsEnabled)
            Button("Save") { vm.save() }
        }
    }
}
