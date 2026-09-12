---
number: SPEC-049
feature: feature-package-dependency-contracts
type: refactor
status: draft
parent: SPEC-010
blocked-by: []
blocking: []
---

# Preserve Dependency Contracts Through Cohesive Feature Packages

## Description

The flow-engine, health-gate, session-context, and source-operation composition code contains two related structural problems:

1. Closely related contracts and implementations are spread across many flat, single-type modules whose names expose implementation suffixes such as `_resolving`, `_reading`, and `_creating` to every consumer.
2. Composition roots sometimes avoid carrying those behavioral objects through the graph. They extract bound methods such as `.resolve`, `.read`, `.make`, `.build`, or `.check`, type them as generic `Callable` values, and inject those functions into downstream services.

The second pattern defeats the purpose of defining a domain protocol. It erases the dependency's meaning, makes constructor contracts less discoverable, and encourages adapters whose only responsibility is reconstructing an object-shaped interface around a method that came from an object.

Related contracts and implementations must instead live in cohesive feature packages with an explicit public API. Consumers depend on the public protocol and receive the behavioral object itself from the composition root.

## Scope

The first migration covers the active chains where project/session context and health-flow construction are currently reduced to callables:

- Session project-context path resolution, directory recording, and directory reading.
- MCP request project-directory resolution propagated into flow catalog, review policy, source search, and source-operation registration.
- Health-check construction currently supplied as `WorkflowHealthCheckerFactory.make`.
- Gate health checking currently supplied as `CodeHealthCheck.check` and wrapped back into an object.
- Hook startup composition flagged by the write gate while converting the session resolver.

The implementation must also audit other bound-method injections in production code and classify each occurrence. Equivalent object-to-method degradation discovered during the audit is included. Generic dispatch and genuine function boundaries are not.

## Package Design

Each migrated capability is organized by cohesive feature, not by one file per protocol:

```text
session/
  agent_start/
    __init__.py
    application.py
    event.py
    event_parser.py
    handler.py
    input_reader.py
    current_directory.py
  project_context/
    __init__.py
    path.py
    directory_reader.py
    directory_recorder.py

harness/
  project_context/
    __init__.py
    request_reader.py
    value.py
```

The exact second-level package names may be adjusted when an existing cohesive package already owns the behavior. The following rules are mandatory:

- `__init__.py` is the public feature facade.
- A protocol lives in the cohesive module containing its first implementation; do not create standalone protocol files or generic `contracts.py` buckets.
- Modules group one cohesive capability and may contain its protocol plus closely related implementations; consumers import the feature package API rather than implementation-suffix modules.
- Code-smell rule CS-2 treats one behavioral contract colocated with its first concrete implementation as one cohesive type boundary. Additional implementations remain separate types in their own modules.
- Do not add compatibility shims for internal imports. Update repository consumers in the same migration and remove obsolete modules.
- Do not create factories solely to construct protocols, data carriers, or simple collaborators.

## Callable Classification

### Must remain objects

- A project-owned object already implements a behavioral protocol and a composition root passes one of its bound methods.
- A constructor accepts a generic callable only to invoke one named domain operation such as `read`, `resolve`, `make`, `build`, or `check`.
- An adapter receives an object's method and recreates substantially the same object-shaped interface.
- A callable type alias hides an existing domain capability.

### May remain callables

- Clocks, UUID generators, environment lookups, path factories, and other system boundary functions.
- Generic higher-order operations whose function is the data being mapped, filtered, retried, or dispatched.
- MCP or command dispatch tables that intentionally map names to handlers.
- Module-level integration functions for external or legacy libraries when there is no existing behavioral object to preserve.

Every retained callable found by the audit must fit one of these categories; the implementation must not mechanically replace all `Callable` annotations.

## Required Behavior

- Session project-context readers and recorders receive a path-resolving object and call `.resolve()` directly.
- MCP project-directory resolution receives a session project-directory reader object and calls `.read()` directly.
- Flow, catalog, review-policy, and source-operation services receive a typed project-directory reader object and call `.read()` directly.
- Health-check coordination receives a typed health-check factory object and calls `.make()` directly.
- Any patch-context adapter receives a typed health checker object and calls `.check()` directly; it must not accept `health_checker.check` as a generic callable.
- The startup hook delegates parsing, environment/context resolution, project recording, and session registration through focused collaborators as required by the gate.
- Runtime behavior, project-root precedence, user-level run persistence, session isolation, and flow outputs remain unchanged.
- Obsolete flat modules, callable aliases, adapters, and dead imports are removed after consumers move to the package API.

## Acceptance Criteria

### AC-1: Feature packages expose cohesive APIs

Given a migrated session or project-context consumer, when it imports the capability, then it imports from the cohesive feature package facade, the protocol lives beside its first implementation, and no standalone one-protocol module or generic contracts bucket is introduced.

Given the write gate reviews such a cohesive module, when it applies CS-2, then the colocated behavioral contract and first implementation are exempt while additional implementations remain independently evaluated.

### AC-2: Session context preserves resolver objects

Given session project context is recorded or read, when the recorder or reader is constructed, then it receives `SessionProjectContextPathResolving` and invokes `.resolve(session_id)` without extracting or accepting a bound method.

### AC-3: Project context remains typed end to end

Given the MCP request resolves a project directory, when flow, review, catalog, and source services consume that directory, then the same `ProjectDirectoryReading` object is propagated through their constructors and no composition root passes `project_directory_reader.read`.

### AC-4: Health construction remains typed end to end

Given a prospective write invokes source-health checking, when the service constructs and invokes its checker, then it receives typed factory and checker objects and no composition root passes `_CHECKER_FACTORY.make` or `CHECK.check`.

### AC-5: Startup hook responsibilities are composed

Given an agent-start payload, when the hook runs, then parsing, session project-context persistence, and optional session registration are performed by focused injected collaborators and `main()` remains only the boundary assembly and invocation point.

### AC-6: Legitimate callables remain explicit

Given a retained callable dependency, when the production audit is reviewed, then it is demonstrably a system boundary, higher-order operation, or dispatch entry rather than a degraded domain object.

### AC-7: Behavior is preserved

Given host environment, recorded session context, and process fallback scenarios, when project resolution runs, then precedence and resolved paths match the pre-refactor behavior exactly.

Given health-gate and flow-engine tests run, when prospective source is reviewed, then run persistence remains under `~/.solid-coder/<project-slug>/runs/` and no project-local operational run directory is introduced.

## Required Tests

- Unit tests pass resolver objects into session project-context readers and recorders and prove their methods are invoked.
- Unit tests pass a session project-directory reader object into MCP request project resolution and cover host, recorded-session, and process fallback precedence.
- Unit tests pass a project-directory reader object through catalog, policy, and source-operation consumers.
- Unit tests prove `CodeHealthCheckService` invokes a health-check factory object rather than a bound method.
- Unit tests prove the gate's patch-context checker delegates to a health checker object rather than a callable.
- Hook integration tests cover valid input, malformed input, absent session ID, project recording, and optional session registration.
- A production audit test or focused static assertion rejects known object-to-bound-method composition patterns without rejecting approved higher-order or boundary callables.
- All non-live tests pass.
- Existing flow-engine and health-gate live smoke contracts remain behaviorally unchanged.

## Affected Components

- `mcp-server/session/`
- `mcp-server/harness/mcp_request_context_project_directory_reader.py`
- Project-directory consumers under `mcp-server/harness/` and `mcp-server/source/`
- `mcp-server/pipeline/flow_run_creator.py`
- `mcp-server/health/code_health_check_service.py`
- `mcp-server/health/code_health_check_adapter.py`
- `mcp-server/health/code_health_check.py`
- `mcp-server/gate/write_gate_coordinator_factory.py`
- `mcp-server/hooks/on_agent_start.py`
- Mirrored tests under `tests/mcp-server/`

## Relationship to Existing Specs

- `SPEC-047` defines isolated health-run lifecycle and direct continuation; this refactor preserves that behavior while correcting its construction boundaries.
- `SPEC-048` defines delegate MCP fail-closed behavior and canonical persistence; this refactor supplies typed project context needed by that fix but does not implement delegate enforcement.
- `SPEC-010` remains the owner of flow orchestration behavior. This spec changes internal organization and dependency representation, not the model-facing YAML or MCP contracts.
