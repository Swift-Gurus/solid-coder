<fix id="UITEST-5" name="Typed Identifiers">

<trigger>
Raw string literals used to query UI elements (`app.buttons["Label"]`,
`.matching(identifier: "string")`, hardcoded system dialog titles).
</trigger>

<strategy severity="MINOR">
Replace 1–2 raw string violations with typed constants. No structural change needed.
</strategy>

<strategy severity="SEVERE">
Create a typed identifier catalogue if none exists. Replace all raw string queries.
System element identifiers must be in the catalogue alongside app-owned ones.
</strategy>

<todo>
**If a typed identifier system already exists:**
- [ ] Replace each raw string query with the typed constant equivalent
- [ ] Add any missing system element identifiers (dialogs, panels) to the catalogue

**If no typed identifier system exists — create one:**
- [ ] Define a nested enum hierarchy reflecting the screen/component structure:
  ```swift
  enum AccessibilityID {
      enum WelcomeScreen {
          static let appTitle = "welcome.appTitle"
          static let openProjectButton = "welcome.openProjectButton"
      }
      enum FilePicker {
          static let panel = "open-panel"           // system-assigned
          static let openButton = "open-panel.open" // system-assigned
      }
  }
  ```
- [ ] Set `accessibilityIdentifier` in production views using the same constants
- [ ] Replace ALL raw string queries in tests with typed constants (partial adoption is a smell)
</todo>

<suggested_fix_must_include>
- Typed identifier enum/catalogue structure
- Before/after of raw string queries replaced with typed constants
- System dialog identifiers catalogued alongside app-owned ones
</suggested_fix_must_include>

</fix>
