<fix id="FM-4" name="solid-stack is incomplete or incorrect">

<trigger>
A frontmatter block's `solid-stack` lists a framework the type doesn't actually
import/use, or omits one it clearly depends on, from: `swiftui`, `uikit`, `appkit`,
`combine`, `structured-concurrency`, `gcd`, `tca`, `core-data`, `swift-data`, `grdb`.
</trigger>

<strategy severity="SEVERE">
Recompute `solid-stack` from the type's actual imports/usages:
- Add an entry for each fixed-vocabulary technology the type genuinely imports or depends on.
- Remove any entry for a technology the type does not use.
- Omit the field entirely if the type is pure language with no framework dependency —
  that is correct, not a violation.
</strategy>

<diagnosis>
For each flagged type, list its actual imports/usages and compare against the
current solid-stack value. Identify extra (unused) entries and missing (used but
undeclared) entries.
</diagnosis>

<todo>
- [ ] List each type with an incorrect solid-stack from the findings
- [ ] For each: list actual imports/usages against the fixed vocabulary
- [ ] Remove entries not actually used
- [ ] Add entries for dependencies that are missing
- [ ] Verify: solid-stack (or its absence) matches the type's real dependencies
</todo>

<suggested_fix_must_include>
- Old solid-stack value → corrected value, per flagged type
- The specific import/usage that justifies each added or removed entry
</suggested_fix_must_include>

</fix>
