"""Publishes deterministic audit events for one finalized review rule."""

from harness.event_appender import EventAppending
from harness.rule_result_event_publishing import RuleResultEventPublishing
from harness.rule_review_result import RuleReviewResult


"""
solid-name: RuleResultEventPublisher
solid-category: service
solid-spec: [SPEC-039]
solid-description: Publishes metric, exception, and result audit events for one finalized review rule.
"""
class RuleResultEventPublisher(RuleResultEventPublishing):
    def __init__(self, event_appender: EventAppending) -> None:
        self._event_appender = event_appender

    def publish(
        self,
        events_path: str,
        result: RuleReviewResult,
    ) -> None:
        for metric in result.metrics:
            self._event_appender.append(
                events_path,
                "metric_scored",
                metric.model_dump(mode="json"),
            )
        self._event_appender.append(
            events_path,
            "exception_classified",
            result.exception.model_dump(mode="json"),
        )
        self._event_appender.append(
            events_path,
            "rule_result_published",
            result.model_dump(mode="json"),
        )
