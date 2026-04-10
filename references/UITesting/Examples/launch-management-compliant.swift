import XCTest

// COMPLIANT: UITEST-1 (Flow Encapsulation) + UITEST-2 (Base Class Structure)
//
// - BaseUITestCase owns app, coordinator, launch, and teardown — test methods inherit all of it
// - OpenProjectFlowCoordinator encapsulates the open-project flow — not duplicated across tests
// - Coordinator composes CleanStateFlowCoordinator for prior-screen navigation
// - All element access goes through typed getX() helpers that wait for existence internally
// - All identifiers are typed paths — no raw strings at any call site
//
// --- Typed helper conventions used in this example ---
//
// coordinator.openProject(at:)
//   └─ Named flow method on the coordinator — encapsulates all steps to reach the dashboard.
//      Accepts file:/line: so failures report at the call site, not inside the coordinator.
//
// app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))
//   └─ getWindow(_:) waits for the window to appear before returning it.
//      projectName(for:) derives the title from the URL — no hardcoded string.

// MARK: - Protocol

protocol FlowCoordinating {
    var app: XCUIApplication { get }
}

// MARK: - Base Class

class BaseUITestCase<Coordinator: FlowCoordinating>: XCTestCase {
    private(set) var app: XCUIApplication!
    private(set) var coordinator: Coordinator!

    override func setUpWithError() throws {
        try super.setUpWithError()
        continueAfterFailure = false
        app = XCUIApplication()
        coordinator = Coordinator(app: app)
        app.launch()
    }

    override func tearDownWithError() throws {
        app.terminate()
        app = nil
        try super.tearDownWithError()
    }
}

// MARK: - Coordinator

struct OpenProjectFlowCoordinator: FlowCoordinating {
    let app: XCUIApplication

    init(app: XCUIApplication) {
        self.app = app
    }

    func openProject(
        at path: String,
        file: StaticString = #file,
        line: UInt = #line
    ) {
        app.clickButton(.button(.welcomeScreen(.openProjectButton)), file: file, line: line)
        let dialog = app.getWindow(.window(.filePicker(.panel)), file: file, line: line)
        dialog.selectFolder(at: path, file: file, line: line)
        let projectName = URL(fileURLWithPath: path).lastPathComponent
        app.getWindow(name: projectName, file: file, line: line)
    }
}

// MARK: - Tests

// COMPLIANT: BaseUITestCase is parameterized with the coordinator that does the work.
// Tests call coordinator.openProject() — no flow logic in the test body.
final class OpenProjectUITests: BaseUITestCase<OpenProjectFlowCoordinator> {

    // COMPLIANT: All launch-state properties verified in one pass.
    // getX() helpers wait for each element internally — no raw strings, no sleep.
    func test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState() {
        app.getImage(.image(.welcomeScreen(.appIcon)))
        app.getStaticText(.staticText(.welcomeScreen(.appTitle)))
        app.getStaticText(.staticText(.welcomeScreen(.tagline)))
        app.getButton(.button(.welcomeScreen(.openProjectButton)))
        app.getGroup(.group(.welcomeScreen(.emptyState)))
    }

    // COMPLIANT: Flow delegated to coordinator — test body only asserts.
    func test_openProject_showsDashboardAndHidesWelcomeScreen() throws {
        let folderURL = try temporaryFolderSupport.createTemporaryFolder(named: "open-project")
        coordinator.openProject(at: folderURL.path)

        app.getWindow(name: temporaryFolderSupport.projectName(for: folderURL))
        app.getGroup(.group(.welcomeScreen(.screen)), shouldBeVisible: false)
    }
}
