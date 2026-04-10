import XCTest

// VIOLATION: UITEST-1 (Flow Encapsulation) + UITEST-2 (Base Class Structure)
//
// Same tests as launch-management-compliant.swift — same scenarios, same typed helpers —
// but wrong structure throughout.
//
// UITEST-2 violations:
// - Inherits directly from XCTestCase — no shared base class
// - XCUIApplication constructed inline in every test — not owned by base
// - app.launch() called in every test — not centralized
//
// UITEST-1 violations:
// - Open project flow (4 steps) inlined in two test methods instead of a coordinator
// - Same navigation sequence duplicated — any change requires editing both tests

final class OpenProjectUITests: XCTestCase {

    // UITEST-2: XCUIApplication constructed and launched inline — repeated in every test
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        let app = XCUIApplication()
        app.launch()

        app.getImage(.image(.welcomeScreen(.appIcon)))
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
        app.getStaticText(.staticText(.welcomeScreen(.tagline)))
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // UITEST-1 + UITEST-2: 4-step open flow inlined — no coordinator, launch in test body
    func test_openProject_showsDashboardAndHidesWelcomeScreen() throws {
        let app = XCUIApplication()
        app.launch()

        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")

        // Duplicated flow — same 4 steps appear in the test below
        app.clickButton(.button(.welcomeScreen(.openProjectButton)))
        let dialog = app.getWindow(.window(.filePicker(.panel)))
        dialog.selectFolder(at: folderURL.path)
        app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))

        app.getGroup(.group(.welcomeScreen(.screen)), shouldBeVisible: false)
    }

    // UITEST-1 + UITEST-2: Same 4-step open flow duplicated — coordinator would eliminate this
    func test_openProject_windowTitleMatchesFolderName() throws {
        let app = XCUIApplication()
        app.launch()

        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")

        // Same flow as test above — duplicated because there is no coordinator to delegate to
        app.clickButton(.button(.welcomeScreen(.openProjectButton)))
        let dialog = app.getWindow(.window(.filePicker(.panel)))
        dialog.selectFolder(at: folderURL.path)
        let window = app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))

        XCTAssertEqual(window.title, temporaryFolderSupport.projectName(for: folderURL))
    }
}
