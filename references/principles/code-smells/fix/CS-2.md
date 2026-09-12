<fix id="CS-2" name="One Class or Struct Per File">

<trigger>
Two or more class or struct definitions found in a single source file, excluding
private extensions that exist solely to support the file's primary type and one
behavioral contract colocated with its first concrete implementation for the
same cohesive capability.
</trigger>

<strategy severity="SEVERE">
Move each additional class or struct into its own file named after the type.
One file = one cohesive type boundary. Private extensions supporting the primary
type may remain, as may one behavioral contract beside its first implementation.
</strategy>

<diagnosis>
List every top-level class and struct in the file.
Identify which is the primary type (the one the file is named after, or the most central one).
Each remaining type is a candidate for extraction unless it is a private helper extension
of the primary type or the first implementation's behavioral contract.
</diagnosis>

<todo>
- [ ] List all top-level class/struct definitions in the file
- [ ] Designate the primary type (keep in the original file)
- [ ] Exempt one behavioral contract colocated with its first implementation
- [ ] For each other secondary type: create a new file named after the type
- [ ] Move the type definition and any directly associated private helpers into the new file
- [ ] Update imports/access modifiers as needed
- [ ] Verify: original file contains exactly one cohesive type boundary
</todo>

<suggested_fix_must_include>
- List of new files to create with their type contents
- Any import or access modifier changes required
- Confirmation of what remains in the original file
</suggested_fix_must_include>

</fix>
