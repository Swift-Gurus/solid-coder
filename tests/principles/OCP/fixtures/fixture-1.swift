import Foundation

class PreferenceSynchronizer {
    func apply(theme: String, fontScale: Double) {
        UserDefaults.standard.set(theme, forKey: "selectedTheme")
        UserDefaults.standard.set(fontScale, forKey: "fontScale")

        NotificationCenter.default.post(
            name: Notification.Name("PreferencesDidChange"),
            object: nil,
            userInfo: ["theme": theme, "fontScale": fontScale]
        )
    }

    func reset() {
        UserDefaults.standard.removeObject(forKey: "selectedTheme")
        UserDefaults.standard.removeObject(forKey: "fontScale")

        NotificationCenter.default.post(
            name: Notification.Name("PreferencesDidChange"),
            object: nil
        )
    }
}
