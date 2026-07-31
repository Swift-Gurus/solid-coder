<fix id="FM-5" name="solid-description violates the description-quality rules">

<trigger>
A frontmatter block's `solid-description` is vague, describes implementation
instead of capability, or (for `abstraction` category) is missing the required
"Contract for..." / "Contract that defines..." prefix.
</trigger>

<strategy severity="SEVERE">
Rewrite `solid-description` as one concise, keyword-rich sentence (or a few) at
the capability level:

- Ask: "would this sentence still be true if the implementation changed entirely?"
  If not, it's describing implementation, not capability.
- Must NOT name any concrete implementation thing: types, variables, APIs, values,
  colors, layout details, composition steps, wiring to other components.
- Must NOT be vague: "A view", "A service", "Handles data" with no substance.
- For `abstraction` category: MUST start with "Contract for..." or "Contract that defines...".
- Include domain terms, structural hints, and key nouns so the type is discoverable via grep.

Good (protocol): "Contract for reading and fetching product data from remote or
local sources. Supports pagination and filtering by category."
Good (implementation): "Resolves a model ID string into a human-readable display
name using a cached lookup table. Handles fallback for unknown model identifiers."
Bad: "implements that default cacheable behaviour, used in MyNetworkProvider and
uses MyStorage, uses DispatchSource, connects with timeout equals 2."
</strategy>

<diagnosis>
For each flagged type, read the current solid-description and identify which rule
it violates: vague, implementation-level, or missing the Contract-for prefix.
</diagnosis>

<todo>
- [ ] List each type with a bad description from the findings, and which rule it violates
- [ ] For each: rewrite as one capability-level sentence, no implementation detail
- [ ] For abstraction category missing the prefix: prepend "Contract for..." / "Contract that defines..."
- [ ] Verify: every solid-description in the file passes all quality rules
</todo>

<suggested_fix_must_include>
- Old solid-description → corrected description, per flagged type
- One-line reason the new description is capability-level, not implementation-level
</suggested_fix_must_include>

</fix>
