<fix id="SUI-8" name="Adaptive Sizing">

<trigger>
`.frame(width:)` or `.frame(height:)` used with a hardcoded literal numeric value.
Fixed frames prevent adaptation to different window sizes, orientations, Dynamic
Type, and localization.
</trigger>

<strategy severity="SEVERE">
Remove hardcoded frames and use the layout system. Choose the proportional approach
based on context.
</strategy>

<todo>
**Child/internal self-sizing** (view hardcodes its own or its sub-elements' size):
- [ ] Remove the `.frame(width:height:)` entirely — let the parent control sizing

**Parent rigid sizing** (parent hardcodes a child's size):
- [ ] Replace with the appropriate proportional approach:
  - `containerRelativeFrame` (preferred, iOS 17+) — when the size should be a fraction of the container. Does not disrupt stack layout negotiation.
  - `frame(minWidth:maxWidth:)` or `frame(minHeight:maxHeight:)` — when you need a flexible range with safety bounds
  - `frame(maxWidth: .infinity)` — when the view should fill available space
  - `GeometryReader` — last resort only. It returns a flexible preferred size that expands greedily, breaking layout negotiation in stacks. Only use when `containerRelativeFrame` is unavailable or when geometry is needed for non-sizing purposes (scroll offsets, position-dependent effects).

**Exceptions (do NOT change):**
- `frame(minWidth:)`, `frame(maxWidth:)`, `frame(idealWidth:)` — constraints, not fixed sizes
- `frame(maxWidth: .infinity)` — explicit flexible fill
- `containerRelativeFrame` — proportional by definition
- `GeometryReader`-based calculations — adaptive by definition
- When the spec/prompt explicitly specifies a fixed size
</todo>

<suggested_fix_must_include>
- Before/after of the hardcoded frame replaced with proportional sizing
- Chosen approach with rationale
</suggested_fix_must_include>

</fix>
