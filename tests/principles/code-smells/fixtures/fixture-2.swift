/**
 solid-name: UserLoading
 solid-category: abstraction
 solid-description: Defines the read boundary of the user-profile loading capability.
 */
protocol UserLoading {
    func loadUser() -> String
}

/**
 solid-name: UserRefreshing
 solid-category: abstraction
 solid-description: Defines the refresh boundary of the same user-profile loading capability.
 */
protocol UserRefreshing {
    func refreshUser() -> String
}

/**
 solid-name: UserLoader
 solid-category: service
 solid-description: Implements user-profile reading and refresh using its file-confined cache entry.
 */
final class UserLoader: UserLoading {
    private var entry = UserCacheEntry(value: "Ada")

    func loadUser() -> String {
        entry.value
    }
}

extension UserLoader: UserRefreshing {
    func refreshUser() -> String {
        entry = UserCacheEntry(value: "Grace")
        return entry.value
    }
}

/**
 solid-name: UserCacheEntry
 solid-category: model
 solid-description: Stores only UserLoader's private profile cache value; it is not a separate public capability.
 */
private struct UserCacheEntry {
    let value: String
}
