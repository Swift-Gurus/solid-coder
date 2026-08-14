final class PreferenceSnapshot {
    let theme: String
    let fontScale: Double

    init(theme: String, fontScale: Double) {
        self.theme = theme
        self.fontScale = fontScale
    }
}

protocol PreferenceSnapshotPublishing {
    func publish(_ snapshot: PreferenceSnapshot)
}

final class PreferenceSnapshotCoordinator {
    private let publisher: PreferenceSnapshotPublishing

    init(publisher: PreferenceSnapshotPublishing) {
        self.publisher = publisher
    }

    func publish(theme: String, fontScale: Double) {
        let snapshot = PreferenceSnapshot(
            theme: theme,
            fontScale: fontScale
        )
        publisher.publish(snapshot)
    }
}
