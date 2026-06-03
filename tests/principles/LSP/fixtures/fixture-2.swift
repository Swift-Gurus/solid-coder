import Foundation

protocol Playback {
    var isPlaying: Bool { get }
    func play()
    func pause()
}

protocol Seekable {
    func seek(to position: TimeInterval)
}

final class LiveStreamPlayer: Playback {
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
}

final class FilePlayer: Playback, Seekable {
    private(set) var isPlaying = false
    private(set) var position: TimeInterval = 0
    private let fileURL: URL

    init(fileURL: URL) {
        self.fileURL = fileURL
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
        self.position = max(0, position)
    }
}
