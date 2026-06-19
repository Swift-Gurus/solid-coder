"""Characterization tests for search.codebase_searcher.

Proves the performance rework (dir pruning, binary sniff, single-pass scan)
preserves matching behaviour: same files match, spec matches still bypass
min_matches, import hits still count per-occurrence, and skip-dirs/binaries
are excluded from results.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search.codebase_searcher import search_raw  # noqa: E402


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class CodebaseSearcherTests(unittest.TestCase):
    def _tree(self, root: Path):
        _write(root, "Fetcher.swift",
               "// solid-description: fetch user data from remote\n"
               "// solid-tags: [networking, user]\n"
               "import Foundation\n"
               "import Combine\n"
               "struct Fetcher {}\n")
        _write(root, "Unrelated.swift",
               "// solid-description: format dates for display\n"
               "import UIKit\n"
               "struct Formatter {}\n")
        _write(root, "SpecFile.swift",
               "// solid-spec: SPEC-042\n"
               "// solid-description: payment processing\n"
               "struct Pay {}\n")
        # File inside a skip dir — must never be scanned.
        _write(root, "Pods/Vendor.swift",
               "// solid-description: fetch user networking user data\n"
               "// solid-tags: [networking, user]\n"
               "import Foundation\n")

    def _paths(self, result):
        return {Path(m["path"]).name for m in result["matches"]}

    def test_tag_match_meets_min_matches(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            # description words {fetch,user,data,remote} + tags {networking,user}
            # + imports {foundation,combine}. tags_lower below hits: desc(fetch,user,data)
            # =3, tags(networking,user)=2, import(foundation)=1 → 6 >= 3.
            res = search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "networking", "foundation"],
                             min_matches=3)
            self.assertIn("Fetcher.swift", self._paths(res))
            self.assertNotIn("Unrelated.swift", self._paths(res))

    def test_below_min_matches_excluded(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = search_raw(sources_dir=str(root), tags=["fetch"], min_matches=3)
            self.assertNotIn("Fetcher.swift", self._paths(res))

    def test_spec_match_bypasses_min_matches(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = search_raw(sources_dir=str(root), spec_numbers=["SPEC-042"], min_matches=99)
            self.assertIn("SpecFile.swift", self._paths(res))
            match = next(m for m in res["matches"] if Path(m["path"]).name == "SpecFile.swift")
            self.assertEqual(match["matched_specs"], ["SPEC-042"])

    def test_skip_dir_never_scanned(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "networking", "foundation"],
                             min_matches=3)
            self.assertNotIn("Vendor.swift", self._paths(res))
            # 3 .swift files at top level; Pods/ pruned from the walk.
            self.assertEqual(res["summary"]["total_files_scanned"], 3)

    def test_build_output_dirs_pruned(self):
        # Vendored dependency checkouts under build-output dirs must be skipped.
        with TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "Mine.swift",
                   "// solid-description: fetch user data\nimport Foundation\nstruct M {}\n")
            for skip in (".derivedData/SourcePackages/Dep.swift", ".gradle/Cached.swift"):
                _write(root, skip,
                       "// solid-description: fetch user data\nimport Foundation\nstruct D {}\n")
            res = search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "foundation"], min_matches=2)
            self.assertEqual(self._paths(res), {"Mine.swift"})
            self.assertEqual(res["summary"]["total_files_scanned"], 1)

    def test_binary_file_skipped(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "blob.swift").write_bytes(
                b"// solid-description: fetch user data networking\x00\x00binary")
            res = search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "networking"],
                             min_matches=1)
            self.assertEqual(res["matches"], [])
            # Still iterated (counted), just not matched.
            self.assertEqual(res["summary"]["total_files_scanned"], 1)

    def test_import_hits_count_per_occurrence(self):
        # Import hits only count for files that have solid- frontmatter.
        # Use frontmatter so the file is eligible; alpha imports add to hit count.
        with TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "Multi.swift",
                   "// solid-description: Alpha consumer\n"
                   "import Alpha\nimport Alpha\nimport Alpha\nstruct X {}\n")
            res = search_raw(sources_dir=str(root), tags=["alpha"], min_matches=3)
            self.assertIn("Multi.swift", self._paths(res))
            res2 = search_raw(sources_dir=str(root), tags=["alpha"], min_matches=5)
            self.assertNotIn("Multi.swift", self._paths(res2))

    def test_multiple_frontmatter_blocks_aggregate(self):
        # The create-type convention puts a solid- block above every type, so a
        # file can carry several blocks separated by large bodies. All blocks
        # must aggregate — this guards against any future head/line-cap that
        # would silently drop frontmatter past the cap.
        with TemporaryDirectory() as d:
            root = Path(d)
            body = "\n".join(f"    let v{i} = {i}" for i in range(200))
            _write(root, "TwoTypes.swift",
                   "// solid-tags: [alpha]\n"
                   "struct First {\n" + body + "\n}\n\n"
                   "// solid-spec: SPEC-777\n"
                   "// solid-tags: [beta]\n"
                   "struct Second {}\n")
            # Tag from the SECOND block (far past any plausible cap) still matches.
            res = search_raw(sources_dir=str(root), tags=["beta"], min_matches=1)
            self.assertIn("TwoTypes.swift", self._paths(res))
            # Spec from the second block still matches.
            res_spec = search_raw(sources_dir=str(root), spec_numbers=["SPEC-777"], min_matches=99)
            self.assertIn("TwoTypes.swift", self._paths(res_spec))

    def test_import_prefilter_does_not_misread_identifiers(self):
        # `importantData` starts with "import" but is not an import declaration;
        # the prefilter fast path must not count it as a hit.
        with TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "Tricky.swift",
                   "let importantData = 5\nlet imported = importantData\nstruct Z {}\n")
            res = search_raw(sources_dir=str(root), tags=["importantdata", "imported"],
                             min_matches=1)
            self.assertNotIn("Tricky.swift", self._paths(res))


if __name__ == "__main__":
    unittest.main()
