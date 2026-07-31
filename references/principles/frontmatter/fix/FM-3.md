<fix id="FM-3" name="solid-category is invalid or blank">

<trigger>
A frontmatter block's `solid-category` is blank, a placeholder, or a value that
doesn't describe a real domain role.
</trigger>

<strategy severity="SEVERE">
Pick the closest match from the known categories:
- `abstraction` — protocols, interfaces, generic type constraints
- `network` — API clients, request/response handling, endpoints
- `viewmodel` — presentation logic driving UI
- `model` — data models, DTOs, entities, value objects
- `view-component` — reusable UI element (row, card, button, cell)
- `screen` — full screen / page
- `modifier` — styling or behavior modifier
- `crud` — object that reads, writes, updates, deletes data
- `utility` — pure functions, formatters, helpers, extensions adding convenience methods
- `navigation` — routing, coordinators, deep linking
- `service` — business logic that doesn't fit any category above
- `unit-test` — unit tests, test helpers, fixtures
- `ui-test` — UI tests, snapshot tests, accessibility tests

If none fit, introduce a new lowercase, hyphenated, noun-like category that
clearly names the domain role — never leave it blank or vague ("misc", "other", "stuff").
</strategy>

<diagnosis>
For each flagged type, read what the type actually does and match it to the
closest category above, or justify a new one.
</diagnosis>

<todo>
- [ ] List each type with an invalid/blank category from the findings
- [ ] For each: determine the correct category from the type's actual responsibility
- [ ] Set solid-category to the chosen value
- [ ] Verify: every solid-category in the file is non-blank and names a real domain role
</todo>

<suggested_fix_must_include>
- Old solid-category value → corrected value, per flagged type, with a one-line reason it fits
</suggested_fix_must_include>

</fix>
