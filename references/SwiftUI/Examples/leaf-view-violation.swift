// VIOLATION: Leaf view that should be stateless but has inline complexity
// SUI-1: avatarSection depth 6 → SEVERE (should extract child leaves)
// SUI-2: 1 impure method (FORMAT) → SEVERE

struct UserAvatarCard: View {
    let name: String
    let avatarURL: URL?
    let joinDate: Date
    let badges: [Badge]
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 8) {
            avatarSection
            Text(name).font(.headline)
            Text(formattedJoinDate)                     // ← uses impure property
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    // SUI-1 SEVERE: nesting depth 6 — should be extracted into child leaves
    private var avatarSection: some View {
        ZStack(alignment: .bottomTrailing) {            // depth 1
            AsyncImage(url: avatarURL) { phase in       // depth 2
                switch phase {
                case .success(let image):
                    image
                        .resizable()
                        .scaledToFill()
                case .failure:
                    ZStack {                            // depth 3
                        Circle()
                            .fill(Color.gray.opacity(0.3))
                        VStack {                        // depth 4
                            Image(systemName: "exclamationmark.triangle")
                            Text("Failed")
                                .font(.caption2)
                        }
                    }
                default:
                    ZStack {                            // depth 3
                        Circle()
                            .fill(Color.gray.opacity(0.3))
                        ProgressView()
                    }
                }
            }
            .frame(width: 80, height: 80)
            .clipShape(Circle())
            .overlay(Circle().stroke(Color.white, lineWidth: 2))
            .shadow(radius: 4)
            .onTapGesture { onTap() }

            // Badge overlay — deep nesting
            VStack(spacing: 2) {                        // depth 3
                ForEach(badges.prefix(3)) { badge in    // depth 4
                    HStack(spacing: 2) {                // depth 5
                        ZStack {                        // depth 6
                            Circle().fill(badge.color)
                            Image(systemName: badge.icon)
                                .font(.system(size: 8))
                                .foregroundColor(.white)
                        }
                        .frame(width: 16, height: 16)
                    }
                }
            }
            .offset(x: 4, y: 4)
        }
    }

    // IMPURE (FORMAT) — date formatting doesn't belong in a leaf view
    // Should be passed as a pre-formatted String from the parent
    private var formattedJoinDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return "Joined " + formatter.string(from: joinDate)
    }
}
