from harness.template_value_rendering import TemplateValueRendering
from health.unavailable_health_metric import UnavailableHealthMetric


"""
solid-name: UnavailableHealthMetricRenderer
solid-category: utility
solid-spec: [SPEC-057]
solid-description: Formats an unavailable health metric and reviewed identity with correction-relevant reasoning while keeping audit evidence private.
"""
class UnavailableHealthMetricRenderer(TemplateValueRendering[UnavailableHealthMetric]):
    def render(self, value: UnavailableHealthMetric) -> str:
        unit = value.provenance.source_unit
        identity = unit.unit_identity if unit is not None else value.rule_instance_id
        return (
            f"{value.workflow_id} / {value.metric.metric_id} ({identity}) — "
            f"{value.metric.additional_info.reasoning}"
        )
