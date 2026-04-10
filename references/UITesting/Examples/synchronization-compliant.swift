import XCTest

// COMPLIANT: UITEST-4 (Synchronization)
//
// - No sleep anywhere — all waiting is condition-based
// - getX() helpers wait for element existence before returning — call chain always
//   includes a condition-based check before any interaction or assertion
//
// --- How condition-based waiting works in this example ---
//
// app.getImage(.image(.welcomeScreen(.appIcon)))
//   └─ getImage(_:) calls waitForExistence(timeout: defaultTimeout) internally.
//      If the element does not appear within the timeout the test fails at the call site.
//      The element is only returned (and asserted on) after existence is confirmed.
//
// app.getWindow(name:)
//   └─ Same pattern — waits for the window to appear before returning it.
//      Reading .title on the returned window is safe: existence was already confirmed.

final class OpenProjectUITests: BaseUITestCase<OpenProjectFlowCoordinator> {

    // COMPLIANT: Each getX() call waits for the element — no sleep, no unguarded access.
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        app.getImage(.image(.welcomeScreen(.appIcon)))
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // COMPLIANT: getWindow(name:) waits for the window to exist before returning it.
    // Reading .title after getWindow() is safe — existence was confirmed in the call chain.
    func test_openProject_windowTitleMatchesFolderName() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")
        coordinator.openProject(at: folderURL.path)

        let window = app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))
        XCTAssertEqual(window.title, temporaryFolderSupport.projectName(for: folderURL))
    }
}
