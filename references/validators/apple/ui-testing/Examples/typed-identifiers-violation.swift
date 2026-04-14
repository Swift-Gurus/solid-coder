import XCTest

// VIOLATION: UITEST-5 (Typed Identifiers)
//
// Same tests as typed-identifiers-compliant.swift — same scenarios, same coordinator —
// but element queries use raw string literals instead of typed constants.
//
// Two violation patterns shown:
// 1. App-owned elements queried by raw string — breaks silently on identifier rename
// 2. System-owned elements (file picker panel) queried by raw title string
//
// Mixed usage is also a violation — using typed constants in some places and raw
// strings in others signals that raw strings will continue to grow.

final class OpenProjectUITests: BaseUITestCase<OpenProjectFlowCoordinator> {

    // UITEST-5: Raw strings for app-owned elements — all of these break silently on rename
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        app.getImage("welcome.appIcon")
        app.getStaticText("welcome.appTitle")
        app.getStaticText("welcome.tagline")
        app.getButton("welcome.openProjectButton")
        app.getGroup("welcome.emptyState")
    }

    // UITEST-5: Raw string for system-owned element (file picker window title)
    // and raw string for the project window — neither is safe from rename
    func test_openProject_showsDashboardAndHidesWelcomeScreen() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")

        app.getButton("welcome.openProjectButton")
        let dialog = app.getWindow("Open")        // system-owned — raw title string
        dialog.selectFolder(at: folderURL.path)
        app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))

        app.getGroup("welcome.screen", shouldBeVisible: false)
    }
}
