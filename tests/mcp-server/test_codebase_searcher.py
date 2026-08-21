"""Characterization tests for typed codebase-search compatibility adapters."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))

from search.codebase_searcher_factory import CodebaseSearcherFactory  # noqa: E402
from search.raw_codebase_searcher_factory import (  # noqa: E402
    RawCodebaseSearcherFactory,
)


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class CodebaseSearcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = CodebaseSearcherFactory().make()
        self.raw_sut = RawCodebaseSearcherFactory().make()

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
            res = self.raw_sut.search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "networking", "foundation"],
                             min_matches=3)
            self.assertIn("Fetcher.swift", self._paths(res))
            self.assertNotIn("Unrelated.swift", self._paths(res))

    def test_below_min_matches_excluded(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = self.raw_sut.search_raw(sources_dir=str(root), tags=["fetch"], min_matches=3)
            self.assertNotIn("Fetcher.swift", self._paths(res))

    def test_spec_match_bypasses_min_matches(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = self.raw_sut.search_raw(sources_dir=str(root), spec_numbers=["SPEC-042"], min_matches=99)
            self.assertIn("SpecFile.swift", self._paths(res))
            match = next(m for m in res["matches"] if Path(m["path"]).name == "SpecFile.swift")
            self.assertEqual(match["matched_specs"], ["SPEC-042"])

    def test_skip_dir_never_scanned(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            self._tree(root)
            res = self.raw_sut.search_raw(sources_dir=str(root),
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
            res = self.raw_sut.search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "foundation"], min_matches=2)
            self.assertEqual(self._paths(res), {"Mine.swift"})
            self.assertEqual(res["summary"]["total_files_scanned"], 1)

    def test_binary_file_skipped(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "blob.swift").write_bytes(
                b"// solid-description: fetch user data networking\x00\x00binary")
            res = self.raw_sut.search_raw(sources_dir=str(root),
                             tags=["fetch", "user", "data", "networking"],
                             min_matches=1)
            self.assertEqual(res["matches"], [])
            self.assertEqual(res["summary"]["total_files_scanned"], 0)

    def test_repeated_imports_count_as_one_distinct_query_match(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "Multi.swift",
                   "// solid-description: Alpha consumer\n"
                   "import Alpha\nimport Alpha\nimport Alpha\nstruct X {}\n")
            res = self.raw_sut.search_raw(sources_dir=str(root), tags=["alpha"], min_matches=1)
            self.assertIn("Multi.swift", self._paths(res))
            res2 = self.raw_sut.search_raw(sources_dir=str(root), tags=["alpha"], min_matches=2)
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
            res = self.raw_sut.search_raw(sources_dir=str(root), tags=["beta"], min_matches=1)
            self.assertIn("TwoTypes.swift", self._paths(res))
            # Spec from the second block still matches.
            res_spec = self.raw_sut.search_raw(sources_dir=str(root), spec_numbers=["SPEC-777"], min_matches=99)
            self.assertIn("TwoTypes.swift", self._paths(res_spec))

    def test_exact_symbols_match_without_frontmatter(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "Tricky.swift",
                   "let importantData = 5\nlet imported = importantData\nstruct Z {}\n")
            res = self.raw_sut.search_raw(sources_dir=str(root), tags=["importantdata", "imported"],
                             min_matches=1)
            self.assertIn("Tricky.swift", self._paths(res))
            match = res["matches"][0]
            self.assertEqual(
                match["description"],
                "No solid-description frontmatter.",
            )

    def test_search_renders_unit_description_and_absolute_inspection_path(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            documented = _write(
                root,
                "Fetcher.swift",
                "// solid-name: Fetcher\n"
                "// solid-description: Fetches remote user data.\n"
                "struct Fetcher {}\n",
            )
            undocumented = _write(
                root,
                "Cache.swift",
                "struct UserCache {}\n",
            )

            result = self.sut.search(
                sources_dir=str(root),
                tags=["Fetcher", "UserCache"],
                min_matches=1,
            )

            self.assertIn("Here is what we found:", result)
            self.assertIn("unit: Fetcher", result)
            self.assertIn("description: Fetches remote user data.", result)
            self.assertIn(f"path: {documented.resolve()}", result)
            self.assertIn("unit: Cache.swift", result)
            self.assertIn(
                "description: No solid-description frontmatter.",
                result,
            )
            self.assertIn(f"path: {undocumented.resolve()}", result)


if __name__ == "__main__":
    unittest.main()
