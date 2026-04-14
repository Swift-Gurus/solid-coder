import XCTest

// VIOLATION: UITEST-4 (Synchronization)
//
// Same tests as synchronization-compliant.swift — same scenarios, same coordinator —
// but element access is not guarded by condition-based waiting.
//
// Two violation patterns shown:
// 1. Thread.sleep used to "wait" before interacting — time-based, not condition-based
// 2. Element queried and accessed directly with no existence check in the call chain

final class OpenProjectUITests: BaseUITestCase<OpenProjectFlowCoordinator> {

    // UITEST-4 (sleep): Thread.sleep used after launch instead of waiting for a specific element.
    // The sleep may be too short on a slow device and too long on a fast one.
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        Thread.sleep(forTimeInterval: 2.0)

        // Accessing elements directly after a fixed delay — no condition checked
        XCTAssertTrue(app.images[.image(.welcomeScreen(.appIcon))].exists)
        XCTAssertTrue(app.staticTexts[.staticText(.welcomeScreen(.appTitle))].exists)
        XCTAssertTrue(app.buttons[.button(.welcomeScreen(.openProjectButton))].exists)
        XCTAssertTrue(app.otherElements[.group(.welcomeScreen(.emptyState))].exists)
    }

    // UITEST-4 (no existence check): coordinator.openProject() navigates to the dashboard,
    // then the window is queried and accessed immediately — nothing in the call chain
    // confirms the window exists before .title is read.
    func test_openProject_windowTitleMatchesFolderName() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")
        coordinator.openProject(at: folderURL.path)

        // Direct property access — no waitForExistence, no getWindow() wrapper
        let window = app.windows[temporaryFolderSupport.projectName(for: folderURL)]
        XCTAssertEqual(window.title, temporaryFolderSupport.projectName(for: folderURL))
    }
}
