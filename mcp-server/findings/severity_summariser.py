"""
solid-description: Aggregates violation severity data into summary statistics and overall status.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol


class SeveritySummarising(Protocol):
    def summarise(self, scored_files: list) -> dict: ...


class SeveritySummariser:
    """Counts severe, minor, and compliant units in a list of scored files."""

    def summarise(self, scored_files: list) -> dict:
        total_units = severe_count = minor_count = compliant_count = 0
        for scored_file in scored_files:
            for unit in scored_file.get("units", []):
                severities = {v["severity"] for v in unit.get("violations", [])}
                if "SEVERE" in severities:
                    severe_count += 1
                elif "MINOR" in severities:
                    minor_count += 1
                else:
                    compliant_count += 1
                total_units += 1
        status = "SEVERE" if severe_count else ("MINOR" if minor_count else "COMPLIANT")
        return {
            "total_units": total_units,
            "severe_count": severe_count,
            "minor_count": minor_count,
            "compliant_count": compliant_count,
            "status": status,
        }
