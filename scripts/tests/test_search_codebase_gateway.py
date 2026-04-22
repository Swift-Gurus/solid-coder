#!/usr/bin/env python3
"""Tests for gateway.py search_codebase command."""

import json
import os
import subprocess
import sys

GATEWAY = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-server", "gateway.py")
FIXTURES = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "validate-plan", "scripts", "test_fixtures"
)


def run_gateway(*args):
    cmd = [sys.executable, GATEWAY, "search_codebase", "--sources-dir", FIXTURES] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return 0, json.loads(result.stdout)
    return result.returncode, result.stderr.strip()


def test_spec_search_returns_matches():
    code, out = run_gateway("--spec-numbers", "SPEC-010")
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths)


def test_synonym_search_comma_separated():
    code, out = run_gateway("--synonyms", "network,fetches,product")
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths)


def test_synonym_single_word():
    """Single synonym (no comma) should not crash — treated as one-element list."""
    code, out = run_gateway("--synonyms", "network")
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths)


def test_min_matches_filters_noise():
    """Broad synonyms + high min-matches should reduce results."""
    _, out_low = run_gateway("--synonyms", "network,fetch,cart,cache,viewmodel,service,data", "--min-matches", "1")
    _, out_high = run_gateway("--synonyms", "network,fetch,cart,cache,viewmodel,service,data", "--min-matches", "3")
    assert out_high["summary"]["files_matched"] <= out_low["summary"]["files_matched"]


def test_min_matches_spec_bypass():
    """Spec matches pass regardless of --min-matches value."""
    code, out = run_gateway("--spec-numbers", "SPEC-010", "--synonyms", "quantum", "--min-matches", "10")
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths)


def test_synonyms_and_spec_combined():
    code, out = run_gateway("--synonyms", "viewmodel,cart", "--spec-numbers", "SPEC-010")
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("CartViewModel" in p for p in paths)
    assert any("ProductFetchService" in p for p in paths)


def test_no_sources_dir_exits_error():
    cmd = [sys.executable, GATEWAY, "search_codebase", "--synonyms", "network"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
