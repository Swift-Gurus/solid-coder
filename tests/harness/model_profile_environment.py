"""Scopes a model-profile override to one integration-session launch."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def model_profile_environment(profile_path: Path) -> Iterator[None]:
    previous = os.environ.get("SOLID_CODER_TEST_MODEL_PROFILE")
    os.environ["SOLID_CODER_TEST_MODEL_PROFILE"] = str(profile_path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SOLID_CODER_TEST_MODEL_PROFILE", None)
        else:
            os.environ["SOLID_CODER_TEST_MODEL_PROFILE"] = previous
