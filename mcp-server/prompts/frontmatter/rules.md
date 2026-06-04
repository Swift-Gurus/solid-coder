Rules for solid-description:
Describe the CAPABILITY — what the type or module does at the interface level,
not how it does it. Ask: "would this sentence still be true if the implementation
changed entirely?" If not, it is describing implementation, not capability.

- One concise sentence at the capability/role level
- Must NOT name any concrete thing inside the implementation: types, variables,
  APIs, values, colors, layout details, composition steps, wiring to other
  components — anything that could change without changing the public contract
- Must NOT be vague: "A view", "A service", "Handles data" with no substance
- For abstraction category: MUST start with "Contract for..." or
  "Contract that defines..."

When fixing:
- Preserve solid-name, solid-category, solid-spec, solid-stack exactly
- Only correct solid-description — touch nothing else
- Do not modify any code or the comment boundary markers
