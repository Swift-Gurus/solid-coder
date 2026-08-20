import Foundation

struct CachedDocument {
    let id: String
    let content: Data
}

final class DocumentCache {
    private var documents: [String: CachedDocument] = [:]

    func store(_ document: CachedDocument) {
        documents[document.id] = document
    }

    func document(id: String) -> CachedDocument? {
        documents[id]
    }
}
