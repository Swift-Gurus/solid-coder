struct PreferenceSnapshot {
    let theme: String
    let fontScale: Double
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
