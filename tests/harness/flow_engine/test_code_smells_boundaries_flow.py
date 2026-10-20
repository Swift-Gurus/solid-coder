"""Exercises the approved CS-2 policy through the real bundled workflow."""

import pytest

import test_code_smells_validation_flow as validation


@pytest.fixture
def scenario():
    subject = validation.TestCodeSmellsValidationFlow(methodName="runTest")
    subject.setUp()
    try:
        yield subject
    finally:
        subject.doCleanups()


@pytest.mark.parametrize("source, associations, expected", [
    ("protocol Loading {}\nclass Loader: Loading {}", [("Loading", "implemented_contract", "Loader")], 1),
    ("protocol Loading {}\nclass Loader {}\nextension Loader: Loading {}", [("Loading", "implemented_contract", "Loader")], 1),
    ("protocol Loading {}\nprotocol Saving {}\nclass Store: Loading, Saving {}",
     [("Loading", "implemented_contract", "Store"), ("Saving", "implemented_contract", "Store")], 1),
    ("protocol Loading {}\nclass Consumer { let dependency: any Loading }",
     [("Loading", "implemented_contract", "Consumer")], 2),
    ("protocol Loading {}\nclass First: Loading {}\nclass Second: Loading {}",
     [("Loading", "implemented_contract", "First")], 2),
    ("class Store {}\nprivate struct Helper {}", [("Helper", "supporting_helper", "Store")], 1),
    ("class Store {}\nfileprivate struct Helper {}", [("Helper", "supporting_helper", "Store")], 1),
    ("class Store {}\nstruct Helper {}", [("Helper", "supporting_helper", "Store")], 2),
    ("class Store {}\nprivate struct Independent {}", [], 2),
    ("protocol Loading {}\nprotocol Saving {}", [("Saving", "cohesive_contract", "Loading")], 1),
    ("protocol Loading {}\nprotocol Networking {}", [], 2),
    ("protocol Loading {}\nprotocol Saving {}\nclass Store: Loading, Saving {}",
     [("Saving", "cohesive_contract", "Loading")], 3),
    ("struct Outer { struct Nested {} }", [], 1),
])
def test_boundary_policy_is_computed_from_source_and_evidenced_relationships(scenario, source, associations, expected):
    scenario.review_unit = source
    ready = scenario._start()
    assert ready.error is None
    output = scenario._response(ready.run_id)
    declarations = scenario._selection(ready.run_id).declarations
    for name, kind, related in associations:
        declaration = next(entry for entry in declarations if entry.unit.name == name)
        owner = next(entry for entry in declarations if entry.unit.name == related)
        index = next(index for index, entry in enumerate(output["classifications"]) if entry["declaration_id"] == declaration.identity)
        output["classifications"][index] = {
            "kind": kind, "declaration_id": declaration.identity,
            "related_declaration_id": owner.identity,
            "additional_info": {"reasoning": "Same cohesive capability.", "evidence": name + " and " + related},
        }
    done = scenario.sut.flow_next({ready.steps[0].instance_id: output})
    assert done.status == "done", done.error
    metric = next(entry for entry in scenario._rule_result(ready.run_id).metrics if entry.metric_id == "CS-2")
    assert metric.value == expected
    assert metric.severity == ("SEVERE" if expected >= 2 else "COMPLIANT")


@pytest.mark.parametrize("source, expected", [
    ("func compose() { if true { print(1) } }", [1, 0, 0]),
    ("class Store { class func compose() { if true { print(1) } } }", [1, 1, 0]),
    ("class Store { func compose() { print(1) } }", [0, 1, 0]),
    ("func outer() { struct Local {} }", [0, 0, 1]),
    ("let closure = { struct Local {} }", [0, 0, 1]),
    ('// struct Fake {}\nlet text = "class Fake {}"', [0, 0, 0]),
])
def test_structural_candidate_scopes_and_literals(scenario, source, expected):
    scenario.review_unit = source
    ready = scenario._start()
    done = scenario.sut.flow_next({ready.steps[0].instance_id: scenario._response(ready.run_id)})
    assert done.status == "done", done.error
    assert [metric.value for metric in scenario._rule_result(ready.run_id).metrics] == expected
