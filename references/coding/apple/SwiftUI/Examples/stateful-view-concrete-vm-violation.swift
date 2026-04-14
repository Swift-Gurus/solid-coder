// VIOLATION: ViewModel injected as concrete class
// SUI-1: COMPLIANT — body depth 2, 4 expressions
// SUI-2: COMPLIANT — 0 impure methods
// SUI-3: COMPLIANT — nested modifier chains <= 2
// SUI-4: SEVERE — concrete ViewModel, not protocol-injected

struct UserProfileView: View {
    @State private var viewModel: UserProfileViewModel // ← concrete class, sealed

    var body: some View {
        ScrollView {
            content
        }
        .overlay {
            if viewModel.isLoading { ProgressView() }
        }
    }

    private var content: some View {
        VStack(spacing: 16) {
            UserAvatarCard(name: viewModel.userName, avatarURL: viewModel.avatarURL, onTap: viewModel.onAvatarTapped)
            FollowerCountBadge(count: viewModel.followerCount)
            Button("Follow") { viewModel.onFollowTapped() }
        }
        .padding()
    }
}
