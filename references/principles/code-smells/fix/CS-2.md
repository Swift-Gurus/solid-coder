<fix id="CS-2" name="One Class or Struct Per File">

<trigger>
Two or more class or struct definitions found in a single source file, excluding
private extensions that exist solely to support the file's primary type.
</trigger>

<strategy severity="SEVERE">
Move each additional class or struct into its own file named after the type.
One file = one type. Private extensions supporting the primary type may remain.
</strategy>

<diagnosis>
List every top-level class and struct in the file.
Identify which is the primary type (the one the file is named after, or the most central one).
Each remaining type is a candidate for extraction unless it is a private helper extension
of the primary type.
</diagnosis>

<todo>
- [ ] List all top-level class/struct definitions in the file
- [ ] Designate the primary type (keep in the original file)
- [ ] For each secondary type: create a new file named `TypeName.swift` (or language equivalent)
- [ ] Move the type definition and any directly associated private helpers into the new file
- [ ] Update imports/access modifiers as needed
- [ ] Verify: original file contains exactly one top-level class or struct
</todo>

<suggested_fix_must_include>
- List of new files to create with their type contents
- Any import or access modifier changes required
- Confirmation of what remains in the original file
</suggested_fix_must_include>

</fix>
