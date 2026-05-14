<fix id="SUI-5" name="Preview-Only View Containment">

<trigger>
A View struct (or its helper types) is declared at file scope but only referenced
from `#Preview` blocks or `PreviewProvider` structs. File-scope structs compile
into the production binary even if only used in previews.
</trigger>

<strategy severity="SEVERE">
Move all preview-only views and their helper types inside the `#Preview` block.
</strategy>

<todo>
- [ ] Identify all file-scope View structs that are PREVIEW_ONLY (only referenced from `#Preview` or `PreviewProvider`, or have zero references)
- [ ] Identify all file-scope helper types (models, mock data, factory types) only used by PREVIEW_ONLY views
- [ ] Move each PREVIEW_ONLY view and its helpers inside the `#Preview { }` block or `PreviewProvider` struct body
- [ ] Update the `#Preview` return to use the now-nested types
- [ ] Verify the file-scope declaration is removed
</todo>

<suggested_fix_must_include>
- `#Preview` block with the view and helpers nested inside
- Removal of the file-scope declaration
- Before/after showing the containment change
</suggested_fix_must_include>

</fix>
