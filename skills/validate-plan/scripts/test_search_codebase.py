#!/usr/bin/env python3
"""Unit tests for search-codebase.py using fixture files."""

import json
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "search-codebase.py")
FIXTURES = os.path.join(os.path.dirname(__file__), "test_fixtures")


def run_script(synonyms=None, sources=None, specs=None, min_matches=None):
    """Run search-codebase.py and return (exit_code, parsed_json_or_stderr)."""
    cmd = [sys.executable, SCRIPT, "--sources", sources or FIXTURES]
    if synonyms is not None:
        cmd += ["--synonyms", json.dumps(synonyms)]
    for spec in (specs or []):
        cmd += ["--spec", spec]
    if min_matches is not None:
        cmd += ["--min-matches", str(min_matches)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return 0, json.loads(result.stdout)
    return result.returncode, result.stderr.strip()


def test_matches_network_synonyms():
    """ProductFetchService should match on 'fetches' (description word) and 'network' (category)."""
    code, out = run_script(["fetches", "network", "product", "retrieve", "load"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService.swift" in p for p in paths), f"Expected ProductFetchService in {paths}"
    match = next(m for m in out["matches"] if "ProductFetchService" in m["path"])
    assert "fetches" in match["matched_terms"]
    assert "network" in match["matched_terms"]
    assert "product" in match["matched_terms"]


def test_matches_cart_synonyms():
    """CartViewModel should match on 'cart' or 'checkout' or 'viewmodel'."""
    code, out = run_script(["cart", "checkout", "viewmodel"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("CartViewModel.swift" in p for p in paths), f"Expected CartViewModel in {paths}"


def test_matches_cache_with_persistence():
    """CacheService should match on 'persistence' (category) or 'cached'."""
    code, out = run_script(["persistence", "cached"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("CacheService.swift" in p for p in paths), f"Expected CacheService in {paths}"


def test_no_frontmatter_excluded():
    """NoFrontmatter.swift should never appear in matches."""
    code, out = run_script(["plain", "model", "string", "foundation"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert not any("NoFrontmatter" in p for p in paths), f"NoFrontmatter should not match: {paths}"


def test_no_matches_for_unrelated_synonyms():
    """Completely unrelated synonyms should yield zero matches."""
    code, out = run_script(["quantum", "blockchain", "synergy"])
    assert code == 0
    assert len(out["matches"]) == 0
    assert out["summary"]["files_matched"] == 0


def test_summary_counts():
    """Summary should report correct totals."""
    code, out = run_script(["network"])
    assert code == 0
    assert out["summary"]["total_files_scanned"] == 7  # 6 original + MultiSpecService
    assert out["summary"]["files_with_frontmatter"] == 6  # 6 files have frontmatter
    assert out["summary"]["files_matched"] == 1  # only ProductFetchService has category "network"


def test_spec_matches_single():
    """--spec SPEC-010 should return ProductFetchService and MultiSpecService."""
    code, out = run_script(specs=["SPEC-010"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService.swift" in p for p in paths), f"Expected ProductFetchService in {paths}"
    assert any("MultiSpecService.swift" in p for p in paths), f"Expected MultiSpecService in {paths}"
    match = next(m for m in out["matches"] if "ProductFetchService" in m["path"])
    assert "SPEC-010" in match["matched_specs"]


def test_spec_matches_multi_spec_file():
    """MultiSpecService has [SPEC-010, SPEC-011] — should match either spec."""
    code, out = run_script(specs=["SPEC-011"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("MultiSpecService.swift" in p for p in paths)
    match = next(m for m in out["matches"] if "MultiSpecService" in m["path"])
    assert "SPEC-011" in match["matched_specs"]


def test_spec_no_match():
    """Unknown spec number yields no matches."""
    code, out = run_script(specs=["SPEC-999"])
    assert code == 0
    assert len(out["matches"]) == 0


def test_spec_multiple_specs_or_logic():
    """--spec SPEC-010 --spec SPEC-011 returns union of matches."""
    code, out = run_script(specs=["SPEC-010", "SPEC-011"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService.swift" in p for p in paths)
    assert any("MultiSpecService.swift" in p for p in paths)


def test_spec_and_synonyms_combined():
    """Combining --spec and --synonyms returns files matching either."""
    code, out = run_script(synonyms=["viewmodel"], specs=["SPEC-010"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService.swift" in p for p in paths)  # from spec
    assert any("CartViewModel.swift" in p for p in paths)  # from synonym


def test_no_args_exits_with_error():
    """Running with neither --synonyms nor --spec should exit 1."""
    cmd = [sys.executable, SCRIPT, "--sources", FIXTURES]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "required" in result.stderr.lower()


def test_invalid_sources_path():
    """Non-existent sources path should exit 1."""
    code, err = run_script(["test"], sources="/nonexistent/path")
    assert code == 1
    assert "not found" in err


def test_invalid_synonyms_json():
    """Invalid JSON for synonyms should exit 1."""
    cmd = [sys.executable, SCRIPT, "--sources", FIXTURES, "--synonyms", "not-json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "invalid" in result.stderr.lower()


def test_multiple_matches_single_run():
    """Broad synonyms should match multiple files."""
    code, out = run_script(["fetch", "network", "cart", "checkout", "persistence", "cached", "viewmodel"])
    assert code == 0
    assert out["summary"]["files_matched"] >= 3  # at least the original 3 frontmatter files


def test_block_comment_frontmatter():
    """BlockCommentService uses /** multi-line block comment */ frontmatter and should match."""
    code, out = run_script(["service", "authentication", "session", "tokens"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("BlockCommentService.swift" in p for p in paths), f"Expected BlockCommentService in {paths}"
    match = next(m for m in out["matches"] if "BlockCommentService" in m["path"])
    assert "service" in match["matched_terms"]
    assert "session" in match["matched_terms"]


def test_multiple_frontmatter_blocks_in_one_file():
    """MultiBlock.swift has two frontmatter blocks — both should contribute matched terms."""
    code, out = run_script(["navigation", "dashboard", "analytics", "screen"])
    assert code == 0
    paths = [m["path"] for m in out["matches"]]
    assert any("MultiBlock.swift" in p for p in paths), f"Expected MultiBlock in {paths}"
    match = next(m for m in out["matches"] if "MultiBlock" in m["path"])
    # 'navigation' comes from first block, 'analytics'/'screen' from second
    assert "navigation" in match["matched_terms"], f"Expected 'navigation' in {match['matched_terms']}"
    assert "screen" in match["matched_terms"], f"Expected 'screen' in {match['matched_terms']}"


def test_multi_block_file_counted_once():
    """A file with multiple frontmatter blocks should be counted once in files_with_frontmatter."""
    code, out = run_script(["view-component"])
    assert code == 0
    # MultiBlock has view-component in first block
    paths = [m["path"] for m in out["matches"]]
    assert any("MultiBlock.swift" in p for p in paths)
    # Should not appear twice
    multi_count = sum(1 for m in out["matches"] if "MultiBlock" in m["path"])
    assert multi_count == 1, f"MultiBlock should appear once, got {multi_count}"


def test_min_matches_default_same_as_one():
    """--min-matches 1 (default) returns same results as omitting the flag."""
    _, out_default = run_script(["network", "product", "cache", "cart"])
    _, out_explicit = run_script(["network", "product", "cache", "cart"], min_matches=1)
    assert out_default["matches"] == out_explicit["matches"]


def test_min_matches_filters_single_term_hits():
    """--min-matches 2 drops files that only matched one synonym."""
    # 'network' alone matches ProductFetchService (category field is a single word).
    # With a broad synonym list including unrelated terms, files matching only 1 term should drop.
    _, out1 = run_script(["network", "quantum", "synergy"], min_matches=1)
    _, out2 = run_script(["network", "quantum", "synergy"], min_matches=2)
    # ProductFetchService matches 'network' only — should appear at min=1 but not min=2
    paths1 = [m["path"] for m in out1["matches"]]
    paths2 = [m["path"] for m in out2["matches"]]
    assert any("ProductFetchService" in p for p in paths1), "Should match at min=1"
    assert not any("ProductFetchService" in p for p in paths2), "Should be filtered at min=2"


def test_min_matches_retains_strong_matches():
    """Files matching many synonyms survive high --min-matches thresholds."""
    # ProductFetchService matches: 'network' (category), 'fetches', 'product', 'data', 'rest', 'api', 'pagination'
    _, out = run_script(["network", "fetches", "product", "data", "rest", "api", "pagination"], min_matches=3)
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths), f"Strong match should survive min=3: {paths}"


def test_min_matches_does_not_filter_spec_matches():
    """--min-matches does not filter files matched by --spec, regardless of synonym hit count."""
    # ProductFetchService has solid-spec: [SPEC-010] but may have few synonym hits
    _, out = run_script(synonyms=["quantum"], specs=["SPEC-010"], min_matches=5)
    paths = [m["path"] for m in out["matches"]]
    assert any("ProductFetchService" in p for p in paths), "Spec match should bypass min-matches filter"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
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
