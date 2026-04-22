---
name: factory-method
displayName: Factory Method
category: creational
description: Construction logic on the target type itself, expressed as a secondary initializer that supplies default dependencies, while the designated initializer still takes every dependency for injection
---

# Factory Method

> Construction logic expressed on the target type itself — a secondary initializer that supplies default dependencies internally, while the designated initializer with full injection remains available for tests and non-default contexts.

---

## Intent

Most production call sites don't want to know how an object is wired. They have a URL, a config, a user — and they want the target. Tests and non-default contexts need to inject every collaborator. Both readers are served when the target type exposes two initializers: a designated one that takes everything, and a secondary one that fills in the defaults.

No new type, no new name, no injection ceremony at the call site — and no sacrifice of testability.

---

## Structure

- The **designated initializer** takes every dependency as a parameter. Tests and custom contexts construct through this path.
- The **secondary initializer** takes only the minimum inputs that the caller owns (typically user data or configuration) and supplies sensible production defaults for every other dependency, delegating to the designated initializer.
- The target type exposes both. Consumers pick based on whether they need to customize.

```swift
final class JSONLineObserver: JSONLineObserving {
    private let reader: any JSONLineReading
    private let notifier: any FileChangeNotifying
    private let sizer: any FileByteSizing

    // Designated — full injection
    init(
        reader: any JSONLineReading,
        notifier: any FileChangeNotifying,
        sizer: any FileByteSizing
    ) {
        self.reader = reader
        self.notifier = notifier
        self.sizer = sizer
    }

    // Factory method — production default wiring
    convenience init(url: URL) {
        self.init(
            reader: JSONLineReader(decoder: MixedKeyJSONDecoder()),
            notifier: FileSystemFileChangeNotifier(url: url),
            sizer: FileByteSizer()
        )
    }
}
```

---

## When to Use

- Production construction is stable — the same set of collaborators is always wired together
- Only user-owned inputs (URL, config, identifiers) vary at the call site
- You want the call site to stay short without introducing a separate factory type
- The collaborators themselves don't need to be swapped across environments

If the construction logic itself must vary across contexts, or the collaborators are policy decisions, reach for a factory type (see `factory.md`) instead.

---

## Anti-pattern

Calling the designated initializer from production code with the full set of dependencies inlined at every call site. The same wiring repeats everywhere; changing a default requires editing every caller. The secondary initializer exists precisely to eliminate that repetition.

Equally wrong: making the secondary initializer the only public constructor and hiding the designated one. Tests and custom contexts then cannot substitute collaborators, and the type loses its testability.

---

## Recognition Conditions

ALL must hold:

1. The construction method lives on the target type itself — not on a separate namespace or factory type
2. Is expressed as a secondary initializer that supplies default values for collaborators the caller does not provide
3. A designated initializer that takes every dependency is still exposed as part of the public API

---

## Related

- `factory.md` — a separate factory type when construction logic itself must be substitutable across contexts.
- `builder.md` — when construction accumulates state across multiple calls before the target is produced.
