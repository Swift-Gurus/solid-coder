"""
solid-name: ModelProfileLoader
solid-category: service
solid-spec: [SPEC-014]
solid-description: Resolves and loads a model profile, returning either a named model's configuration or the project default when no name is supplied.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
for _p in (_HARNESS_DIR, _HOOKS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from interfaces import ModelProfileLoading, TomlLoading  # noqa: E402
from models import ModelProfile  # noqa: E402
from solid_coder_paths import CONFIG_DIR, CONFIG_LOCAL_TOML  # noqa: E402


class ModelProfileLoader(ModelProfileLoading):
    def __init__(
        self,
        project_root: Path,
        toml_loader: TomlLoading,
        profile_dir: "Path | None" = None,
    ) -> None:
        self._project_root = project_root
        self._toml_loader = toml_loader
        self._profile_dir = profile_dir or (project_root / "tests" / "models")

    def load(self, model_name: str | None) -> ModelProfile:
        if model_name is not None:
            profile_path = self._profile_dir / (model_name + ".toml")
            if not profile_path.exists():
                raise RuntimeError(f"Model profile not found: {profile_path}")
            data = self._toml_loader.load_toml(profile_path)
            return ModelProfile(
                output_dir_name=model_name,
                profile_path=profile_path,
                llm=data.get("llm", {}),
                inference=data.get("inference", {}),
            )
        project_toml = self._project_root / CONFIG_DIR / CONFIG_LOCAL_TOML
        data = self._toml_loader.load_toml(project_toml)
        llm = data.get("llm", {})
        backend = llm.get("backend", "claude")
        return ModelProfile(
            output_dir_name=backend,
            profile_path=project_toml if project_toml.exists() else None,
            llm=llm,
            inference=data.get("inference", {}),
        )