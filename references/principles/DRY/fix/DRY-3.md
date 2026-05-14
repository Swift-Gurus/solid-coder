<fix id="DRY-3" name="Missing Abstraction — Embedded Infrastructure">

<trigger>
A domain type embeds generic infrastructure logic (retry, caching, pagination,
serialisation) inline instead of delegating to a reusable abstraction.
</trigger>

<strategy severity="SEVERE">
Identify the generic pattern within the domain type, extract it into a standalone
reusable type or component, and update the domain type to delegate to it.
Priority: check for an existing abstraction in the codebase before creating one.
</strategy>

<diagnosis>
Read the missing-abstraction table from findings (pattern type: behavioral, creational,
UI composition, data flow). Identify the infrastructure concern embedded in the domain type.
</diagnosis>

<todo>
- [ ] Identify the pattern category:
  - **Behavioral** (retry, polling, rate-limiting) → extract to a policy type (e.g. `RetryPolicy`, `Paginator`)
  - **Creational** (factory logic, object graph construction) → extract to a factory or builder
  - **UI composition** (repeated layout/modifier logic) → extract to a reusable view component or ViewModifier
  - **Data flow** (transformation pipelines, mapping chains) → extract to a transformer or mapper type
- [ ] Search the codebase for an existing reusable abstraction (`search_codebase`) — prefer reuse over creation
- [ ] Extract the infrastructure logic into a focused standalone type:
  - The type should be domain-agnostic (parameterised by callbacks, generics, or protocol dependencies)
  - The domain type injects and delegates to the extracted type
- [ ] Update the domain type to remove the embedded infrastructure and delegate to the extracted abstraction
- [ ] Predict post-fix: 0 embedded infrastructure patterns; domain type contains only domain logic
</todo>

<suggested_fix_must_include>
- Extracted reusable abstraction (the infrastructure type/component)
- Updated domain type delegating to it via injection
- Before/after showing the embedded logic removed from the domain type
</suggested_fix_must_include>

</fix>
