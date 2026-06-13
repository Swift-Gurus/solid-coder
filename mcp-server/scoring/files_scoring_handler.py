"""
solid-description: Evaluates code units across files for compliance with quality principles and reports violations.
solid-category: service
solid-tags: [utility, service]
"""

import html
import re
from typing import Any, Protocol

from scoring.principle_scorer import PrincipleScorerProviding


class FilesScoringCapable(Protocol):
    def score_files(self, scorer_provider: PrincipleScorerProviding, files: list) -> tuple: ...


_CONDITION_VAR_RE = re.compile(r'\b([a-z][a-z0-9_]*)\b')
_CONDITION_EXTRACT_RE = re.compile(r'<condition>(.*?)</condition>', re.DOTALL)
_PYTHON_KEYWORDS = frozenset({"and", "or", "not", "in", "is", "True", "False", "None"})


def _condition_var_names(bands_xml: str) -> set:
    """Extract identifier names used in severity-band condition expressions."""
    names: set = set()
    for cond in _CONDITION_EXTRACT_RE.findall(bands_xml):
        for m in _CONDITION_VAR_RE.finditer(html.unescape(cond)):
            name = m.group(1)
            if name not in _PYTHON_KEYWORDS:
                names.add(name)
    return names


class FilesScoringHandler:
    """Scores units in a list of files using principles from the metrics object."""

    def score_files(self, scorer_provider: PrincipleScorerProviding, files: list) -> tuple:
        if not hasattr(files, "__iter__") or hasattr(files, "lower"):
            return [], {"error": "'files' must be a list of file objects"}
        scored_files = []
        for file_obj in files:
            scored_units = []
            for unit in file_obj.get("units", []):
                metrics_by_principle = unit.get("metrics", {})
                unit_violations: list = []
                _file_path = file_obj.get("file_path", "?")
                _unit_name = unit.get("unit_name", "?")

                for principle_name, principle_metrics in metrics_by_principle.items():
                    if not isinstance(principle_metrics, dict):
                        continue
                    scorer, error, _folder = scorer_provider.scorer_for(principle_name)
                    if error:
                        return scored_files, {
                            "error": f"{_file_path}, unit {_unit_name}: {error['error']}"
                        }

                    flat: dict[str, Any] = {
                        var: entry["value"]
                        for var, entry in principle_metrics.items()
                        if isinstance(entry, dict) and "value" in entry
                    }

                    for metric_id in scorer.known_metric_ids:
                        r = scorer.score_unit(flat, metric_id, _file_path)
                        if "error" in r:
                            return scored_files, {
                                "error": (
                                    f"{_file_path}, unit {_unit_name}: metric variable missing "
                                    f"during {metric_id} evaluation. Ensure all required fields "
                                    f"are present per the <submission-metrics-example>. "
                                    f"({r['error']})"
                                )
                            }
                        if r["final_severity"] != "COMPLIANT":
                            unit_violations.append({
                                "rule_id": metric_id,
                                "severity": r["final_severity"],
                            })

                scored_unit = dict(unit)
                scored_unit["violations"] = unit_violations
                scored_units.append(scored_unit)

            scored_file = dict(file_obj)
            scored_file["units"] = scored_units
            scored_files.append(scored_file)

        return scored_files, None
