<fix id="CS-1" name="No Static Logic for Splitting Responsibilities">

<trigger>
One or more static methods, class methods, or module-level functions contain business logic
(branching, construction, or transformation) rather than delegating to an instance.
</trigger>

<strategy severity="SEVERE">
Replace the static function with instance-based alternatives:

- If the caller always needs the same defaults → add a convenience `init` with default
  arguments on the concrete type. Callers that omit parameters get the defaults; callers
  that need different behavior inject their own.

- If callers need different configurations → extract a dedicated factory type whose
  `init` accepts the configuration and exposes instance methods for construction.

Do NOT create a static factory method on the type itself.
</strategy>

<diagnosis>
Identify every static member that contains logic beyond returning a constant.
For each: determine whether callers need the same defaults (convenience init fix)
or different configurations (factory type fix).
</diagnosis>

<todo>
- [ ] List all static methods with business logic from the findings
- [ ] For each: decide convenience init vs factory type
- [ ] Convenience init path: add `init` with default parameter values matching the static logic
- [ ] Factory type path: create a new type (e.g. `FooFactory`) with `init` taking config, instance method `make() -> Foo`
- [ ] Update all call sites to use the new init or factory instance
- [ ] Remove the static method
- [ ] Verify: no remaining static members with logic; only `static let` constants remain
</todo>

<suggested_fix_must_include>
- Concrete before/after of the static method being removed
- New `init` signature or factory type definition
- Updated call site showing the new construction pattern
</suggested_fix_must_include>

</fix>
