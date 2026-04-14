import XCTest

// COMPLIANT: UITEST-3 (Assertion Grouping) + UITEST-4 (Waiting Strategy)
//
// - All launch-state properties asserted in a single test — one app launch, one pass
// - Tests that have different preconditions remain separate
// - Each distinct screen state gets exactly one test that asserts all its properties
//
// --- Typed helper conventions used in this example ---
//
// app.getGroup(.group(.welcomeScreen(.screen)))
//   └─ getGroup(_:)         — XCUIApplication extension that:
//                              1. Resolves the typed identifier path to a string
//                              2. Calls waitForExistence(timeout: defaultTimeout) on the element
//                              3. Fails the test at the call site if the element does not appear
//                              4. Returns the XCUIElement for further interaction if needed
//
// .group(.welcomeScreen(.screen))
//   └─ Typed identifier path from the accessibility catalogue (e.g. AppResources).
//      No raw strings — renaming an identifier is a compile error, not a silent test break.
//
// app.clickButton(.button(...))
//   └─ Same pattern as getGroup — waits for existence, then taps. Never taps blindly.

final class WelcomeScreenUITests: BaseUITestCase<CleanStateFlowCoordinator> {
    private lazy var openFlow = OpenProjectFlowCoordinator(app: app)

    // COMPLIANT: All launch-state properties in one pass — 5 properties, 1 launch.
    // Each getX() call waits for the element internally — no explicit sleep needed.
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        app.getImage(.image(.welcomeScreen(.appIcon)))
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
        app.getStaticText(.staticText(.welcomeScreen(.tagline)))
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // COMPLIANT: Different precondition (project opened, then closed) — separate test is correct.
    // This state cannot be reached from launch alone, so it cannot be merged with the test above.
    func test_afterClosingProject_welcomeScreenShowsRecentRow() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "recent-test")
        coordinator.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)

        app.getGroup(.group(.welcomeScreen(.screen)))
        // projectName(for:) derives the name from the URL — no hardcoded string
        app.getGroup(.group(.welcomeScreen(.recentProjectRow(name: temporaryFolderSupport.projectName(for: folderURL)))))
    }

    // COMPLIANT: Different precondition (clear action performed) — separate test is correct.
    func test_clearButton_removesAllRowsAndShowsEmptyState() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "clear-test")
        openFlow.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)
        app.getGroup(.group(.welcomeScreen(.screen)))

        app.clickButton(.button(.welcomeScreen(.clearButton)))

        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }
}
