import Foundation

protocol PreferenceStoring {
    func set(_ value: Any?, forKey key: String)
    func removeObject(forKey key: String)
}

protocol ChangeBroadcasting {
    func broadcast(name: String, info: [String: Any]?)
}

class PreferenceSynchronizer {
    private let store: PreferenceStoring
    private let broadcaster: ChangeBroadcasting

    init(store: PreferenceStoring, broadcaster: ChangeBroadcasting) {
        self.store = store
        self.broadcaster = broadcaster
    }

    func apply(theme: String, fontScale: Double) {
        store.set(theme, forKey: "selectedTheme")
        store.set(fontScale, forKey: "fontScale")
        broadcaster.broadcast(
            name: "PreferencesDidChange",
            info: ["theme": theme, "fontScale": fontScale]
        )
    }

    func reset() {
        store.removeObject(forKey: "selectedTheme")
        store.removeObject(forKey: "fontScale")
        broadcaster.broadcast(name: "PreferencesDidChange", info: nil)
    }
}
