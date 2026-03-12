// VIOLATION: Stateful view with business logic, no ViewModel, no protocols
// SUI-1: body depth 5, 11 expressions → SEVERE
// SUI-2: 4 impure methods (FORMAT, FORMAT, COMPUTE, DATA_FETCH) → SEVERE

struct UserProfileView: View {
    let userId: String
    @State private var user: User?
    @State private var isLoading = false
    @State private var isFollowing = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Inline avatar — should be a leaf view
                ZStack {
                    Circle()
                        .fill(Color.gray.opacity(0.3))
                    if let url = user?.avatarURL {
                        AsyncImage(url: url) { image in
                            image.resizable()                    // depth 5
                        } placeholder: {
                            ProgressView()
                        }
                    }
                }
                .frame(width: 80, height: 80)
                .clipShape(Circle())

                Text(user?.name ?? "Loading...")
                    .font(.title2)
                Text(formattedBio)
                Text(followerText)
                    .foregroundColor(.secondary)

                HStack(spacing: 12) {
                    Button("Follow") { toggleFollow() }
                    Button("Edit") { /* navigation mixed in view */ }
                }

                if let error {
                    Text(error).foregroundColor(.red)
                    Button("Retry") { loadProfile() }
                }
            }
            .padding()
        }
        .overlay {
            if isLoading { ProgressView() }
        }
        .task { loadProfile() }
    }

    // IMPURE (FORMAT) — should be in ViewModel
    private var formattedBio: String {
        guard let bio = user?.bio else { return "" }
        return bio.count > 100 ? String(bio.prefix(100)) + "..." : bio
    }

    // IMPURE (FORMAT) — should be in ViewModel
    private var followerText: String {
        guard let count = user?.followers else { return "" }
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return (formatter.string(from: NSNumber(value: count)) ?? "\(count)") + " followers"
    }

    // IMPURE (COMPUTE) — should be in ViewModel
    private func toggleFollow() {
        isFollowing.toggle()
        // Optimistic update + API call mixed together
        Task {
            do {
                try await URLSession.shared.data(from: URL(string: "https://api.example.com/follow/\(userId)")!)
            } catch {
                isFollowing.toggle() // rollback
                self.error = error.localizedDescription
            }
        }
    }

    // IMPURE (DATA_FETCH) — should be in ViewModel
    private func loadProfile() {
        isLoading = true
        Task {
            do {
                let (data, _) = try await URLSession.shared.data(
                    from: URL(string: "https://api.example.com/users/\(userId)")!
                )
                let decoded = try JSONDecoder().decode(User.self, from: data)
                user = decoded
                isLoading = false
            } catch {
                self.error = error.localizedDescription
                isLoading = false
            }
        }
    }
}
