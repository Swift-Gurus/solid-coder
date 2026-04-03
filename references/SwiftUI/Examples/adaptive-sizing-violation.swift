// SUI-8 Violation: Adaptive Sizing
// Views use hardcoded literal frame values instead of proportional sizing.

import SwiftUI

// --- Violation 1: Child self-sizing ---
// BrandingPanel hardcodes its own width internally.
// The parent (WelcomeScreen) should decide how wide this panel is.

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
        .frame(width: 240) // 🔥 SUI-8: child deciding its own external size
        .padding(.all, 24)
    }

    private var appIcon: some View {
        Image("AppIcon")
            .resizable()
            .frame(width: 80, height: 80) // 🔥 SUI-8: hardcoded literal on internal element
            .cornerRadius(12)
    }

    private var title: some View {
        Text("My App")
            .font(.title)
    }

    private var openButton: some View {
        Button("Open Project...", action: onOpenProject)
            .frame(width: 200) // 🔥 SUI-8: hardcoded literal on internal element
    }
}

// --- Violation 2: Parent rigid sizing ---
// WelcomeScreen hardcodes child sizes instead of using proportional layout.

struct WelcomeScreen: View {
    var body: some View {
        HStack(spacing: 0) {
            BrandingPanel(onOpenProject: {})
                .frame(width: 240) // 🔥 SUI-8: parent hardcoding child size

            Divider()

            RecentProjectsList()
                .frame(width: 620) // 🔥 SUI-8: parent hardcoding child size
        }
        .frame(width: 860, height: 520) // 🔥 SUI-8: hardcoded window size
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
// - BrandingPanel.body: .frame(width: 240) — child self-sizing
// - appIcon: .frame(width: 80, height: 80) — literal on internal element
// - openButton: .frame(width: 200) — literal on internal element
// - WelcomeScreen: .frame(width: 240) on BrandingPanel — parent rigid sizing
// - WelcomeScreen: .frame(width: 620) on RecentProjectsList — parent rigid sizing
// - WelcomeScreen: .frame(width: 860, height: 520) — parent rigid sizing
// Fixed frame violations: 6 → SEVERE
