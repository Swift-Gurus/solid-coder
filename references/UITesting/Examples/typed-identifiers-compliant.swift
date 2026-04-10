import XCTest

// COMPLIANT: UITEST-5 (Typed Identifiers)
//
// - All element queries use typed identifier paths — app-owned and system-owned
// - No raw string appears at any call site
// - Renaming an identifier is a compile error, not a silent test break
//
// --- How typed identifiers work in this example ---
//
// .image(.welcomeScreen(.appIcon))
//   └─ Nested enum path from the accessibility catalogue (e.g. AppResources).
//      Resolves to the string set as accessibilityIdentifier in the production view.
//      The same constant is used in both the view and the test — one rename updates both.
//
// .window(.filePicker(.panel))
//   └─ System-owned elements are catalogued too — the NSOpenPanel window identifier
//      assigned by macOS is a constant in the same catalogue, not a hardcoded string.

final class OpenProjectUITests: BaseUITestCase<OpenProjectFlowCoordinator> {

    // COMPLIANT: All app-owned elements referenced via typed paths — no raw strings
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        app.getImage(.image(.welcomeScreen(.appIcon)))
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
        app.getStaticText(.staticText(.welcomeScreen(.tagline)))
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // COMPLIANT: System-owned file picker window also uses a typed path — not a raw title string
    func test_openProject_showsDashboardAndHidesWelcomeScreen() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")
        coordinator.openProject(at: folderURL.path)

        app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))
        app.getGroup(.group(.welcomeScreen(.screen)), shouldBeVisible: false)
    }
}
