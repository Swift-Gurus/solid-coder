<fix id="DRY-2" name="Inlined Duplication">

<trigger>
The same logical sequence or algorithm appears in 2+ places — copy-pasted logic that
should be a shared abstraction.
</trigger>

<strategy severity="SEVERE">
Extract the duplicated logic into a shared function, method, or type. All duplication
sites call the shared abstraction.
</strategy>

<diagnosis>
Read the duplication table from findings (locations, duplicated sequence).
Identify the common logical structure and what varies between sites (if anything).
</diagnosis>

<todo>
- [ ] Identify the shared logical sequence (the part that is identical or near-identical)
- [ ] Identify what varies between duplication sites (parameters, types, return values)
- [ ] Choose the appropriate abstraction level:
  - **Same types, same logic** → shared `func` or `method`
  - **Different types, same algorithm** → generic function or protocol with default implementation
  - **Different types, same structure** → protocol with associated types or generics
- [ ] Check for existing abstractions before creating new ones — can an existing utility cover this?
- [ ] Extract the shared abstraction to an appropriate location (shared module, extension, utility file)
- [ ] Replace all duplication sites with calls to the shared abstraction
- [ ] Predict post-fix: 0 inlined duplications; all sites use the shared abstraction
</todo>

<suggested_fix_must_include>
- The extracted shared function/type/generic with the common logic
- Before/after of one duplication site showing replacement with the shared call
- Note on where the shared abstraction lives (file/module)
</suggested_fix_must_include>

</fix>
