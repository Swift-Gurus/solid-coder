// COMPLIANT: Stateful view with State + Actions protocols, ViewModel behind interfaces
// SUI-1: body depth 2, 4 expressions → COMPLIANT
// SUI-2: 0 impure methods → COMPLIANT
// SUI-3: nested modifier chains <= 2 → COMPLIANT

// MARK: - State Protocol (what the view reads)

protocol UserProfileState: Observable {
    var userName: String { get }
    var avatarURL: URL? { get }
    var bio: String { get }
    var followerCount: String { get }
    var isLoading: Bool { get }
    var error: String? { get }
}

// MARK: - Actions Protocol (what the view triggers)

protocol UserProfileActions {
    func onAvatarTapped()
    func onFollowTapped()
    func onEditProfileTapped()
    func onRetry()
}

// MARK: - View (dumb — binds State to UI, forwards gestures to Actions)
// Proper injection of view model as separated interfaces
struct UserProfileView<State: UserProfileState>: View {
    let state: State
    let actions: UserProfileActions

    var body: some View {
        ScrollView {
            content
        }
        .overlay {
            if state.isLoading { ProgressView() }
        }
    }

    // PURE_VIEW — composes child leaves
    private var content: some View {
        VStack(spacing: 16) {
            headerSection
            footerSection
        }
        .padding()
    }

    // PURE_VIEW — avatar + bio
    private var headerSection: some View {
        VStack(spacing: 12) {
            UserAvatarCard(
                name: state.userName,
                avatarURL: state.avatarURL,
                onTap: actions.onAvatarTapped
            )
            ProfileBioSection(bio: state.bio)
        }
    }

    // PURE_VIEW — badge + actions
    private var footerSection: some View {
        VStack(spacing: 12) {
            FollowerCountBadge(count: state.followerCount)
            actionButtons
        }
    }

    // PURE_VIEW — returns some View, no logic
    private var actionButtons: some View {
        HStack(spacing: 12) {
            Button("Follow") { actions.onFollowTapped() }
            Button("Edit") { actions.onEditProfileTapped() }
        }
    }
}

// Alternative approach for Proper injection of view model as single object, applicable for small VMs
struct UserProfileViewSingleVM<VM: UserProfileState & UserProfileActions>: View {
    let vm: VM

    var body: some View {
        // body implementation
    }
}

// MARK: - ViewModel (conforms to both protocols)

@Observable
final class UserProfileViewModel: UserProfileState, UserProfileActions {
    // State
    private(set) var userName: String = ""
    private(set) var avatarURL: URL?
    private(set) var bio: String = ""
    private(set) var followerCount: String = ""
    private(set) var isLoading: Bool = false
    private(set) var error: String?

    private let userService: UserServiceProtocol
    private let router: RouterProtocol
    private let userId: String

    init(userId: String, userService: UserServiceProtocol, router: RouterProtocol) {
        self.userId = userId
        self.userService = userService
        self.router = router
    }

    // Actions
    func onAvatarTapped() {
        guard let url = avatarURL else { return }
        router.navigate(to: .fullScreenImage(url))
    }

    func onFollowTapped() {
        Task { await toggleFollow() }
    }

    func onEditProfileTapped() {
        router.navigate(to: .editProfile(userId))
    }

    func onRetry() {
        Task { await loadProfile() }
    }

    // Internal logic — lives here, not in the view
    func loadProfile() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let user = try await userService.fetchUser(id: userId)
            userName = user.name
            avatarURL = user.avatarURL
            bio = user.bio
            followerCount = "\(user.followers)"
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func toggleFollow() async {
        do {
            try await userService.toggleFollow(userId: userId)
        } catch {
            self.error = error.localizedDescription
        }
    }
}

// MARK: - Protocols for dependencies

protocol UserServiceProtocol {
    func fetchUser(id: String) async throws -> User
    func toggleFollow(userId: String) async throws
}

protocol RouterProtocol {
    func navigate(to destination: Destination)
}
