<fix id="OCP-1" name="Sealed Variation Points">

<trigger>
1+ concrete dependencies that are hardcoded and NOT behind abstractions (sealed points).
</trigger>

<strategy severity="SEVERE">
Introduce a protocol for each sealed point; inject the dependency via `init` instead
of constructing or referencing it directly.
Priority order: reuse > extend > adapt > wrap.
</strategy>

<diagnosis>
Read the sealed points from the findings. For each sealed concrete dependency:
1. Check if a protocol already exists for it → use it
2. Check if the type can conform via extension → add extension conformance (preferred over a wrapper)
3. For framework/system singletons (`.shared`, `.default`): if the returned type can be
   instantiated or subclassed, use extension conformance + inject the instance. Only if
   truly static-only (enum, global function) → Boundary Adapter
4. If none apply → create a minimal adapter/wrapper
</diagnosis>

<todo>
- [ ] For each sealed point in findings:
  - [ ] **Check for existing protocols** — search before creating new ones
    - If exists → use it
    - If not → create protocol (name + minimal method signatures the caller needs)
  - [ ] **Check existing type conformance**
    - Type already provides exact methods → add extension conformance
    - Can forward via chained call → extension conformance with forwarding impl (prefer over wrapper)
    - Cannot conform (system type, no meaningful identity) → adapter/wrapper struct
    - Static-only API (enum, global func) → Boundary Adapter (exempt from OCP-1)
  - [ ] **Update original class** — replace sealed reference with protocol-typed `init` parameter; remove internal construction
- [ ] Predict post-fix: 0 sealed points, all dependencies are protocol-typed
</todo>

<suggested_fix_must_include>
- Protocol definition (or reference to existing protocol)
- Extension conformance OR adapter struct (whichever applies)
- Modified original class with `init(dependency: DependencyProtocol)` and removed direct construction
- Before/after of the sealed reference site
</suggested_fix_must_include>

</fix>
