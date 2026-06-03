import Foundation

protocol DocumentService {
    func open(id: String) -> Document?
    func list(folder: String) -> [Document]
    func search(query: String) -> [Document]
    func metadata(id: String) -> [String: String]
    func preview(id: String) -> Data?

    func create(_ document: Document, folder: String)
    func update(id: String, content: Data)
    func rename(id: String, to name: String)
    func move(id: String, to folder: String)
    func delete(id: String)
}

struct Document {
    let id: String
    let name: String
    let content: Data
}

final class ArchiveBrowser: DocumentService {
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

    func metadata(id: String) -> [String: String] {
        guard let document = index[id] else { return [:] }
        return [
            "name": document.name,
            "size": String(document.content.count)
        ]
    }

    func preview(id: String) -> Data? {
        guard let document = index[id] else { return nil }
        return document.content.prefix(256)
    }

    func create(_ document: Document, folder: String) { }
    func update(id: String, content: Data) { }
    func rename(id: String, to name: String) { }
    func move(id: String, to folder: String) { }
    func delete(id: String) { }
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

    func metadata(id: String) -> [String: String] {
        guard let document = store[id] else { return [:] }
        return ["name": document.name, "size": String(document.content.count)]
    }

    func preview(id: String) -> Data? {
        return store[id]?.content.prefix(256)
    }

    func create(_ document: Document, folder: String) {
        store[document.id] = document
        layout[folder, default: []].append(document.id)
    }

    func update(id: String, content: Data) {
        guard let existing = store[id] else { return }
        store[id] = Document(id: existing.id, name: existing.name, content: content)
    }

    func rename(id: String, to name: String) {
        guard let existing = store[id] else { return }
        store[id] = Document(id: existing.id, name: name, content: existing.content)
    }

    func move(id: String, to folder: String) {
        for key in layout.keys {
            layout[key]?.removeAll { $0 == id }
        }
        layout[folder, default: []].append(id)
    }

    func delete(id: String) {
        store[id] = nil
        for key in layout.keys {
            layout[key]?.removeAll { $0 == id }
        }
    }
}
