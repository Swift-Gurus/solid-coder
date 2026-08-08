"""Declares the local model profile for reusable integration-test contracts."""

from typing import ClassVar


"""
solid-name: LocalTestBase
solid-category: test-support
solid-description: Supplies the local model-profile selection shared by live flow-engine and principle health-check integration tests.
"""
class LocalTestBase:

    MODEL_PROFILE: ClassVar[str] = "local"
