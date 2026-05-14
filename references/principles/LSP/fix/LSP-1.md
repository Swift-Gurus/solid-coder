<fix id="LSP-1" name="Type Check / Typecast">

<trigger>
1+ runtime type checks (`is`, `as?`, `as!`, `type(of:)`) against concrete subtypes in
client code that uses a base type or protocol.
</trigger>

<strategy severity="SEVERE">
Eliminate the type check by improving the abstraction. The client should never need to
know which subtype it has. Pattern: protocol extraction + generic constraints, or adding
the required behaviour to the protocol.
</strategy>

<diagnosis>
Read the type check locations from the findings. For each:
- What behaviour does the client need that triggered the check?
- Is that behaviour missing from the protocol/base type?
- Can it be added to the protocol, or does it require a generic constraint?
</diagnosis>

<todo>
- [ ] For each type check:
  - [ ] Identify what the check enables (e.g. calling a method only available on one subtype)
  - [ ] Add that capability to the protocol/base type
    - Capability is universal → add to protocol with a sensible default implementation
    - Behaviour is subtype-specific → use a generic constraint (`func process<T: Processor>(_ item: T)`)
    - Check is framework-forced (e.g. `response as? HTTPURLResponse`) → mark as exception, do not change
  - [ ] Replace the type-check site with a direct protocol method call or generic parameter
  - [ ] Remove the `is`/`as?` check
- [ ] Predict post-fix: 0 net type checks; client code operates on the protocol/base only
</todo>

<suggested_fix_must_include>
- Updated protocol definition with the new/expanded method or associated type
- Generic function signature replacing the type-switch site
- Before/after of the type-check block showing its removal
</suggested_fix_must_include>

</fix>
