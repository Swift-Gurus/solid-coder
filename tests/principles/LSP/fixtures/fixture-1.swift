import Foundation

protocol MediaPlayer {
    var isPlaying: Bool { get }
    func play()
    func pause()
    func seek(to position: TimeInterval)
}

final class LiveStreamPlayer: MediaPlayer {
    private(set) var isPlaying = false
    private let endpoint: URL

    init(endpoint: URL) {
        self.endpoint = endpoint
    }

    func play() {
        guard !isPlaying else { return }
        isPlaying = true
    }

    func pause() {
        guard isPlaying else { return }
        isPlaying = false
    }

    func seek(to position: TimeInterval) {
        fatalError("seek is not available for live streams")
    }
}
