"""Tests the typed cleanup hook boundary."""

import unittest

from pipeline_cleanup.pipeline_cleanup_event import PipelineCleanupEvent


"""
solid-name: TestPipelineCleanupEvent
solid-category: unit-test
solid-description: Verifies cleanup hook inputs retain optional transcript paths and ignore unrelated host event fields.
"""
class TestPipelineCleanupEvent(unittest.TestCase):
    def test_missing_transcript_has_no_cleanup_target(self) -> None:
        self.assertIsNone(PipelineCleanupEvent.model_validate({}).transcript_path)

    def test_null_transcript_has_no_cleanup_target(self) -> None:
        self.assertIsNone(PipelineCleanupEvent.model_validate({"transcript_path": None}).transcript_path)

    def test_host_fields_do_not_change_the_transcript_target(self) -> None:
        event = PipelineCleanupEvent.model_validate({"transcript_path": "/project/session.jsonl", "session_id": "host-session"})
        self.assertEqual(event.transcript_path, "/project/session.jsonl")
