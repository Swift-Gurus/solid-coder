
protocol StorageItem {}

protocol Storage {
    func saveItem(_ item: StorageItem)
}

final class StorageImpl: Storage {
   let database: Database
   func saveItem(_ item: StorageItem) {
      if let user = item as? User {
             let json = // create json from user
             let record = Record(user.id, attributes: json)
             try database.save(record)
         } else if let product = item as? Product {
              let json = // create json from product
              let record = Record(product.id, attributes: json)
             try database.save(record)
         } else if let order = item as? Order {
             let json = // create json from order
             let record = Record(order.id, attributes: json)
             try database.save(record)
         }
   }
}