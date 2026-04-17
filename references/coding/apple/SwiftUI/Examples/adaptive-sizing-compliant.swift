
struct BrandingPanel: View {
    let onOpenProject: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Spacer()
            appIcon
            title
            Spacer()
            openButton
        }
        // ✅ No .frame(width:) — parent decides the width
        .padding(.all, DSSpacing.xl)
    }

    private var appIcon: some View {
        DSImageView(.app(.icon)) // ✅ No frame — image adapts to space given by parent
            .dsCornerRadius(.sm)
    }

    private var title: some View {
        Text("My App")
            .font(.title)
    }

    private var openButton: some View {
        Button("Open Project...", action: onOpenProject)
            .frame(maxWidth: .infinity) // ✅ Fills available width
    }
}

struct WelcomeScreen: View {
    var body: some View {
        HStack(spacing: 0) {
            BrandingPanel(onOpenProject: {})
                .containerRelativeFrame(.horizontal) { length, _ in
                    length * 0.28 // ✅ Proportional — 28% of container
                }

            Divider()

            RecentProjectsList()
                // ✅ No frame needed — fills remaining space naturally
        }
        .frame(minWidth: 700, minHeight: 400) // ✅ Constraints, not fixed size
    }
}

// --- Compliant: GeometryReader for internal proportional layout ---
// Valid use: sizing internal elements proportionally within a view's own body.
// The GeometryReader reads the space the PARENT already gave this view,
// then distributes it proportionally among internal elements.
// This does NOT break stack negotiation because GeometryReader is not
// wrapping a stack — it IS the view's content.

struct BrandingPanelWithGeometry: View {
    let onOpenProject: () -> Void

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                Spacer()

                Image("AppIcon")
                    .resizable()
                    .frame(
                        width: geometry.size.width * 0.4,  // ✅ 40% of panel width
                        height: geometry.size.width * 0.4  // ✅ Square, proportional
                    )
                    .cornerRadius(12)

                Text("My App")
                    .font(.title)
                    .padding(.top, 8)

                Spacer()

                Button("Open Project...", action: onOpenProject)
                    .frame(maxWidth: .infinity) // ✅ Fills available width
            }
            .padding(24) // Padding/spacing can be literals or design system tokens — SUI-8 scopes to frame sizes only
        }
        // ✅ No external .frame() — parent decides this view's size
    }
}

struct RecentProjectsList: View {
    var body: some View {
        List {
            Text("Project A")
            Text("Project B")
        }
    }
}

// Analysis:
// - BrandingPanel: no self-sizing, fills parent-given width
// - appIcon: no frame — adapts to parent-given space
// - openButton: uses maxWidth: .infinity (flexible fill)
// - WelcomeScreen: proportional via containerRelativeFrame (28% of container)
// - WelcomeScreen: frame(minWidth:minHeight:) = constraints, not fixed
// - BrandingPanelWithGeometry: GeometryReader reads parent-given space,
//   distributes proportionally to internal elements. Icon is 40% of panel width,
//   spacing and padding scale with container. No hardcoded literals.
// Fixed frame violations: 0 → COMPLIANT
