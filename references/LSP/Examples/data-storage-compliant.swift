
protocol Identifiable {
   var id: String { }
}

protocol RecordRepresentable: Identifiable, Encodable {

}

protocol Storage {
    func saveItem<T: RecordRepresentable>(_ item: T)
}

final class StorageImpl: Storage {
   let database: Database
   func saveItem<T: RecordRepresentable>(_ item: T) {
      let data = try JSONEncoder().encode(item)
      let json = try JSONSerialization.jsonObject(data) as? [String: Any] ?? [:]
      let record = Record(item.id, attributes: json)
      try database.save(record)
   }
}
