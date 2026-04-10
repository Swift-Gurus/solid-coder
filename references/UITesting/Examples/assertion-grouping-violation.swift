import XCTest

// VIOLATION: UITEST-3 (Assertion Grouping)
//
// Same tests as assertion-grouping-compliant.swift, same helpers, same screens —
// but assertions for each screen state are fragmented across separate test methods.
// Each state is entered multiple times when one pass would cover all properties.

final class WelcomeScreenUITests: BaseUITestCase<CleanStateFlowCoordinator> {
    private lazy var openFlow = OpenProjectFlowCoordinator(app: app)

    // VIOLATION: Five separate tests all start from launch with no setup, each asserting one property.
    // The app launches 5 times for the same screen state — one test could assert all five.
    func test_launchState_showsAppIcon() {
        app.getImage(.image(.welcomeScreen(.appIcon)))
    }

    func test_launchState_showsTitle() {
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
    }

    func test_launchState_showsTagline() {
        app.getStaticText(.staticText(.welcomeScreen(.tagline)))
    }

    func test_launchState_showsOpenProjectButton() {
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
    }

    func test_launchState_showsEmptyState() {
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // VIOLATION: Two separate tests navigate the same flow (open project → close → welcome screen)
    // to assert one property each. The flow runs twice when one test could assert both.
    func test_afterClosingProject_showsScreen() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "recent-test")
        coordinator.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)

        app.getGroup(.group(.welcomeScreen(.screen)))
    }

    func test_afterClosingProject_showsRecentRow() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "recent-test")
        coordinator.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)

        app.getGroup(.group(.welcomeScreen(.recentProjectRow(name: temporaryFolderSupport.projectName(for: folderURL)))))
    }

    // VIOLATION: Two separate tests run the same flow (open → close → clear) to assert one property each.
    func test_clearButton_hidesRows() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "clear-test")
        openFlow.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)
        app.getGroup(.group(.welcomeScreen(.screen)))
        app.clickButton(.button(.welcomeScreen(.clearButton)))

        app.getGroup(.group(.welcomeScreen(.recentProjectRow(name: temporaryFolderSupport.projectName(for: folderURL))), shouldBeVisible: false))
    }

    func test_clearButton_showsEmptyState() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "clear-test")
        openFlow.openProject(at: folderURL.path)
        app.emulateShortcut(.closeWindow)
        app.getGroup(.group(.welcomeScreen(.screen)))
        app.clickButton(.button(.welcomeScreen(.clearButton)))

        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }
}
