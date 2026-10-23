import pytest
import test_lsp_validation_flow as validation
import yaml
from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: test_lsp_fatal_call_policy
solid-category: integration-test
solid-spec: [SPEC-067]
solid-description: Exercises deterministic fatal-call findings in the real LSP workflow even when model classifications omit crashing helpers or claim a NoOp exception.
"""


@pytest.fixture
def scenario():
    subject = validation.TestLSPValidationFlow(methodName="runTest")
    subject.setUp()
    try:
        yield subject
    finally:
        subject.doCleanups()


@pytest.mark.parametrize(
    "source, expected",
    [
        ('class Loader { func load() { fatalError("unsupported") } }', 1),
        (
            'class Loader { func load(_ invalid: Bool) { if invalid { fatalError("invalid") } } }',
            1,
        ),
        (
            'class Loader { func load() { parse() }; private func parse() { fatalError("unsupported") } }',
            1,
        ),
        (
            'protocol Loading { func load() }\nclass Loader: Loading { func load() { parse() }; private func parse() { fatalError("unsupported") } }',
            1,
        ),
        ('class Loader { init() { Swift.fatalError("unavailable") } }', 1),
        ('class NoOpLoader { func load() { fatalError("unsupported") } }', 1),
        (
            'class Loader { func load() { /* fatalError("comment") */ print("fatalError(text)") } }',
            0,
        ),
    ],
)
@pytest.mark.parametrize("is_exception", [False, True])
@pytest.mark.parametrize("aggregate", [False, True])
def test_actual_fatal_calls_cannot_be_hidden_by_an_empty_model_inventory(
    scenario, source, expected, is_exception, aggregate
):
    scenario.prepared = (
        PrepareReviewOperationFactory()
        .make()
        .execute(
            PrepareReviewInput(
                target=TextAnalysisSource(
                    text=source,
                    virtual_path=str(scenario.project_root / "Loader.swift"),
                ),
            )
        )
    )
    scenario.unit = next(
        unit
        for unit in scenario.prepared.units
        if unit.target.name in {"Loader", "NoOpLoader"}
    )
    if aggregate:
        workflow = scenario.project_root / "workflow.yaml"
        workflow.write_text(
            yaml.safe_dump(
                {
                    "id": "aggregate-lsp",
                    "name": "Aggregate LSP",
                    "max_turns": 10,
                    "execution": {"mode": "aggregate"},
                    "presentation": {"mode": "combined"},
                    "steps": [
                        {
                            "include": {"workflow": "lsp"},
                            "as": "review",
                            "with": {
                                "review_unit": "{{params.review_unit}}",
                                "source_context": "{{params.source_context}}",
                            },
                        }
                    ],
                }
            )
        )
        started = scenario.sut.flow_start(
            str(workflow),
            {
                "review_unit": scenario.unit.model_dump(mode="json"),
                "source_context": scenario.prepared.source_context.model_dump(
                    mode="json"
                ),
            },
        )
    else:
        started = scenario._start()
    assert started.error is None, started.error
    ready = scenario.sut.flow_next(
        _submission(
            started.steps[0],
            {
                "has_inheritance": False,
                "relationship_terms": [scenario.unit.target.name],
                "contract_implementations": [],
            },
        )
    )
    assert ready.error is None, ready.error
    inventory = next(
        event["outputs"]
        for event in scenario._events(started.run_id)
        if event.get("event") == "step_completed"
        and (event.get("local_step_id") or event["step_id"])
        == "prepare_contract_members"
    )
    if inventory["members"]:
        assert [member["name"] for member in inventory["members"]] == ["load"]
        assert (
            ready.steps[0].batch.authored_step.step_id
            if aggregate
            else ready.steps[0].step_id
        ) == "analyze_substitutability"
        ready = scenario.sut.flow_next(
            _submission(
                ready.steps[0],
                {
                    "has_inheritance": False,
                    "relationship_terms": [scenario.unit.target.name],
                    "contract_implementations": [
                        {
                            "member": inventory["members"][0]["identity"],
                            "classification": "MEANINGFUL",
                            "evidence": "Loader.load() calls private parse(), whose body calls fatalError(unsupported).",
                        }
                    ],
                },
            )
        )
        assert ready.error is None, ready.error
    assert len(ready.steps) == 1
    assert (
        ready.steps[0].batch.authored_step.step_id
        if aggregate
        else ready.steps[0].step_id
    ) == "classify_exception"
    done = scenario.sut.flow_next(
        _submission(
            ready.steps[0],
            {
                "is_exception": is_exception,
                "additional_info": {"reasoning": "Not exempt.", "evidence": source},
            },
        )
    )
    assert done.status == "done", done.error
    result = next(
        rule
        for rule in scenario._aggregate_result(started.run_id).rule_results
        if rule.workflow_id == "lsp"
    )
    metric = next(
        metric
        for metric in result.metrics
        if metric.metric_id == "LSP-3" and metric.observation_id == "fatal_calls"
    )
    assert metric.value == expected
    assert metric.severity == ("SEVERE" if expected else "COMPLIANT")


def _submission(step, outputs):
    if isinstance(step.batch, AggregateBatchStepPresentation):
        batch = step.batch
        return {
            batch.label: {batch.workflow_alias: {batch.authored_step.step_id: outputs}}
        }
    return {step.instance_id: outputs}
