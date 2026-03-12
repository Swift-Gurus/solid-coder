// COMPLIANT: Leaf views — stateless, just render data passed in
// No @State, no @Binding, no ViewModel — pure rendering functions
// Composed of smaller leaf views for complex UI elements
//
// Each struct reviewed independently against:
// SUI-1: nesting < 3, expressions < 5
// SUI-2: 0 impure methods
// SUI-3: nested modifier chains <= 2 per child

// MARK: - UserAvatarCard (leaf — composed of child leaves)

struct UserAvatarCard: View {
    let name: String
    let avatarURL: URL?
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 8) {
            RoundedAvatarImage(url: avatarURL, size: 80)
                .onTapGesture { onTap() }
            Text(name)
                .font(.headline)
        }
    }
}

// MARK: - RoundedAvatarImage (child leaf — handles avatar styling)

struct RoundedAvatarImage: View {
    let url: URL?
    let placeholderSystemName = "person.fill"
    var body: some View {
        AsyncImage(url: url) { image in
            image
                .resizable()
                .scaledToFill()
        } placeholder: {
            placeholder
        }
        .clipShape(Circle())
        .overlay(Circle().stroke(Color.white, lineWidth: 2))
        .shadow(radius: 4)
    }

    @ViewBuilder
    var placeholder: some View {
          Circle()
          .fill(Color.gray.opacity(0.3))
          .overlay(Image(systemName: "person.fill")
          .foregroundColor(.gray))
    }
}

// MARK: - ProfileBioSection (leaf)

struct ProfileBioSection: View {
    let bio: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            aboutText
            bioText
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private var bioText: some View {
         Text(bio).font(.body)
    }

    @ViewBuilder
    private var aboutText: some View {
        Text("About")
           .font(.subheadline)
           .foregroundColor(.secondary)
    }
}

// MARK: - FollowerCountBadge (leaf)

struct FollowerCountBadge: View {
    let count: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "person.2.fill")
                .foregroundColor(.blue)
            Text(count)
                .font(.subheadline)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.1))
        .cornerRadius(16)
    }

}
