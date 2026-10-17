"""Preserves exact requirement accounting for the retained candidate-review workflow."""

import textwrap

import pytest

import test_isp_validation_flow as isp_validation

from harness.project_context import ProjectDirectory
from source.analysis.operations.discover_source_declaration_input import DiscoverSourceDeclarationInput
from source.analysis.operations.source_declaration_discovery_operation_factory import SourceDeclarationDiscoveryOperationFactory


@pytest.fixture
def scenario():
    case = isp_validation.TestISPValidationFlow(methodName="runTest")
    case.setUp()
    try:
        yield case
    finally:
        case.doCleanups()


def coverage_payload(scenario, run_id, step):
    matches = next(
        event["outputs"]["matches"] for event in scenario._events(run_id)
        if event.get("event") == "step_completed"
        and event.get("step_id") == step.step_id.removesuffix("classify_candidate") + "match"
    )
    entries = [
        {
            "observation_id": match["requirement"]["identity"],
            "matches": index < 5,
            "included": True,
            "reasoning": "MEANINGFUL" if index < 5 else "EMPTY",
            "evidence": match["requirement"]["name"],
        }
        for index, match in enumerate(matches)
    ]
    return {
        "availability": {
            "observation_id": "ArchiveBrowser", "matches": True, "included": True,
            "reasoning": "All implementations inspected.", "evidence": "Canonical fixture.",
        },
        "coverage_entries": entries,
    }


def add_submission(submissions, step, payload):
    if step.batch is None:
        submissions[step.instance_id] = payload
    else:
        assert step.batch.mode.value == "aggregate"
        submissions.setdefault(step.batch.label, {}).setdefault(step.batch.workflow_alias, {})[
            step.batch.authored_step.step_id
        ] = payload


@pytest.mark.parametrize("aggregate", [False, True])
@pytest.mark.parametrize("fault", ["missing", "empty", "duplicate", "unknown", "excluded"])
def test_rejects_invalid_requirement_accounting_before_scoring_and_recovers(scenario, fault, aggregate):
    discovery = SourceDeclarationDiscoveryOperationFactory(
        ProjectDirectory(path=scenario.project_root),
    ).make().execute(DiscoverSourceDeclarationInput(
        target=scenario._parameters.review_unit.target,
        context=scenario._parameters.source_context,
    ))
    wrapper = scenario.project_root / "coverage.yaml"
    child = """- include: {workflow: isp-candidate-review}
  as: candidate_reviews
  depends_on: [seed]
  for_each: "{{steps.seed.outputs.candidates}}"
  with:
    candidate: "{{item}}"
    inventory: "{{params.inventory}}"
    protocol_name: "{{params.protocol_name}}"
"""
    steps = (
        "- group: reviews\n  execution: {mode: aggregate}\n  presentation: {mode: combined}\n  steps:\n"
        + textwrap.indent(child, "    ")
        if aggregate else child
    )
    wrapper.write_text(
        "id: coverage-test\nname: Retained candidate coverage\nmax_turns: 10\nsteps:\n"
        + "  - id: seed\n    prompt: Return the test discovery candidates.\n    outputs:\n"
        + "      - name: candidates\n        type: data\n        schema: {type: array, items: {type: object}}\n"
        + textwrap.indent(steps, "  "),
        encoding="utf-8",
    )
    started = scenario.sut.flow_start(str(wrapper), {
        "inventory": discovery.inventory.model_dump(mode="json"),
        "protocol_name": scenario._parameters.review_unit.target.name,
    })
    assert started.error is None
    run_id = started.run_id
    started = scenario.sut.flow_next({started.steps[0].instance_id: {
        "candidates": [candidate.model_dump(mode="json") for candidate in discovery.related_declarations],
    }})
    assert started.error is None
    if aggregate:
        assert len(started.steps) == 2
    step = started.steps[0]
    assert step.step_id.endswith("classify_candidate")
    payload = coverage_payload(scenario, run_id, step)
    entries = payload["coverage_entries"]
    invalid = [entry.copy() for entry in entries]
    if fault == "missing":
        invalid.pop()
    elif fault == "empty":
        invalid.clear()
    elif fault == "duplicate":
        invalid.append(invalid[0].copy())
    elif fault == "unknown":
        invalid[0]["observation_id"] = "unknown-requirement"
    else:
        invalid[0]["included"] = False

    submissions = {}
    for sibling in started.steps[1:]:
        add_submission(submissions, sibling, coverage_payload(scenario, run_id, sibling))
    add_submission(submissions, step, {**payload, "coverage_entries": invalid})
    rejected = scenario.sut.flow_next(submissions)

    assert rejected.error is None
    retry = next(item for item in rejected.steps if item.step_id == step.step_id)
    assert retry.rejection_reason
    if fault != "excluded":
        assert "complete replacement" in retry.rejection_reason
        assert ("missing" if fault == "empty" else fault) in retry.rejection_reason
    assert not any(
        event.get("event") == "step_completed"
        and event.get("step_id") == step.step_id.removesuffix("classify_candidate") + "coverage_ratio"
        for event in scenario._events(run_id)
    )

    corrected = {}
    add_submission(corrected, retry, payload)
    accepted = scenario.sut.flow_next(corrected)

    assert accepted.error is None
    assert all(item.step_id != step.step_id for item in accepted.steps)
    ratio = next(
        event["outputs"] for event in scenario._events(run_id)
        if event.get("event") == "step_completed"
        and event.get("step_id") == step.step_id.removesuffix("classify_candidate") + "coverage_ratio"
    )
    assert ratio["denominator_count"] == len(entries)
    assert ratio["value"] == 0.5
    match_id = step.step_id.removesuffix("classify_candidate") + "match"
    assert len([
        event for event in scenario._events(run_id)
        if event.get("event") == "step_completed" and event.get("step_id") == match_id
    ]) == 1
    for sibling in started.steps[1:]:
        assert all(item.step_id != sibling.step_id for item in accepted.steps)
        completions = [
            event for event in scenario._events(run_id)
            if event.get("event") == "step_completed" and event.get("step_id") == sibling.step_id
        ]
        assert len(completions) == 1
