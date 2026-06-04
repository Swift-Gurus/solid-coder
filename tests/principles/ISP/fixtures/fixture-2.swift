import Foundation

struct Document {
    let id: String
    let name: String
    let content: Data
}

protocol DocumentReading {
    func open(id: String) -> Document?
    func list(folder: String) -> [Document]
    func search(query: String) -> [Document]
}

protocol DocumentWriting {
    func create(_ document: Document, folder: String)
    func update(id: String, content: Data)
    func delete(id: String)
}

protocol DocumentService: DocumentReading, DocumentWriting {}

final class ArchiveBrowser: DocumentReading {
    private let index: [String: Document]
    private let folders: [String: [String]]

    init(index: [String: Document], folders: [String: [String]]) {
        self.index = index
        self.folders = folders
    }

    func open(id: String) -> Document? {
        return index[id]
    }

    func list(folder: String) -> [Document] {
        let ids = folders[folder] ?? []
        return ids.compactMap { index[$0] }
    }

    func search(query: String) -> [Document] {
        return index.values.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }
}

final class WorkspaceEditor: DocumentService {
    private var store: [String: Document]
    private var layout: [String: [String]]

    init(store: [String: Document], layout: [String: [String]]) {
        self.store = store
        self.layout = layout
    }

    func open(id: String) -> Document? {
        return store[id]
    }

    func list(folder: String) -> [Document] {
        let ids = layout[folder] ?? []
        return ids.compactMap { store[$0] }
    }

    func search(query: String) -> [Document] {
        return store.values.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }

    func create(_ document: Document, folder: String) {
        store[document.id] = document
        layout[folder, default: []].append(document.id)
    }

    func update(id: String, content: Data) {
        guard let existing = store[id] else { return }
        store[id] = Document(id: existing.id, name: existing.name, content: content)
    }

    func delete(id: String) {
        store[id] = nil
        for key in layout.keys {
            layout[key]?.removeAll { $0 == id }
        }
    }
}
