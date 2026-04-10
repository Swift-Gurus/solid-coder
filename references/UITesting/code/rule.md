# UI Testing Coding Gotchas

Common mistakes the code agent makes when writing UI tests.

---

## 1. Coordinator methods must forward `file` and `line`

Every coordinator method containing assertions must accept `file: StaticString = #file, line: UInt = #line` and pass them to every assertion and helper call. Without this, failures report inside the coordinator — not at the test call site.

```swift
func openProject(at path: String, file: StaticString = #file, line: UInt = #line) {
    app.clickButton(.button(.welcomeScreen(.openProjectButton)), file: file, line: line)
    app.getWindow(.window(.filePicker(.panel)), file: file, line: line)
}
```

---

## 2. Coordinator never creates `XCUIApplication()` internally

Always receive `app` via `init(app: XCUIApplication)`.

---

## 3. `continueAfterFailure = false` must be set in base class setUp

Without it a test continues after a failed assertion — interactions after a failed `getX()` produce cascading crashes and misleading failures.

---

## 4. `app.activate()` does not simulate a Dock icon click

`app.activate()` does not trigger `applicationShouldHandleReopen`. Target the Dock directly:

```swift
XCUIApplication(bundleIdentifier: "com.apple.dock").icons[AppConstants.appName].click()
```

---

## 5. UserDefaults — named suite and `#if DEBUG` reset (required for UI test state isolation)

When writing app code that will be exercised by UI tests, two rules apply:

1. **App must use a named suite** — all persistent state goes through `UserDefaults(suiteName:)`, not `.standard`. Without a named suite there is no way to reset only app state between tests.

2. **Reset must be behind `#if DEBUG`** — any code that checks for a reset-state launch argument and calls `removePersistentDomain(forName:)` must be wrapped in `#if DEBUG` so it never compiles into release builds.

```swift
#if DEBUG
if processInfoArguments.contains(AppConstants.LaunchArguments.resetState) {
    userDefaults.removePersistentDomain(forName: AppConstants.UserDefaultsSuite.suiteName)
    userDefaults.synchronize()
}
#endif
```

