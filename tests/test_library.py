import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skill_library.core import LibraryError, inspect_tree, read_records, safe_relative
from skill_library.fetch import fetch
from skill_library.operations import add, doctor, extract_archive, init, rebuild_indexes, reorganize, search, trust


def make_skill(root, name, body="Use this skill.", extra=b"payload"):
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Helps with {name}.\n---\n\n{body}\n", encoding="utf-8")
    (folder / "assets").mkdir()
    (folder / "assets" / "data.bin").write_bytes(extra)
    return folder


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "library"
        init(self.root)

    def test_init_twice_and_indexes(self):
        init(self.root)
        self.assertEqual(read_records(self.root), [])
        self.assertTrue(rebuild_indexes(self.root, [], check=True)["ok"])

    def test_import_full_bundle_duplicate_and_move(self):
        src = make_skill(self.base / "source", "alpha")
        first = add(self.root, str(src), "Development/Frontend")["results"][0]
        self.assertEqual(first["status"], "added")
        self.assertEqual(add(self.root, str(src))["results"][0]["status"], "duplicate")
        rec = read_records(self.root)[0]
        self.assertEqual((self.root / rec["path"] / "assets" / "data.bin").read_bytes(), b"payload")
        self.assertTrue(doctor(self.root)["ok"])
        result = reorganize(self.root, rec["id"], "Media/Tools")
        self.assertEqual(result["to"], "Media/Tools/alpha")
        self.assertTrue(doctor(self.root)["ok"])
        self.assertFalse((self.root / "Development" / "INDEX.md").exists())

    def test_same_name_different_content(self):
        a = make_skill(self.base / "a", "alpha", extra=b"a")
        b = make_skill(self.base / "b", "alpha", extra=b"b")
        add(self.root, str(a), "Tools")
        add(self.root, str(b), "Tools")
        records = read_records(self.root)
        self.assertEqual(len(records), 2)
        self.assertEqual(len({r["path"] for r in records}), 2)
        self.assertTrue(all((self.root / r["path"]).is_dir() for r in records))

    def test_fetch_isolation_and_trust(self):
        src = make_skill(self.base / "source", "alpha")
        add(self.root, str(src))
        rec = read_records(self.root)[0]
        project_a = self.base / "a"
        project_b = self.base / "b"
        project_a.mkdir()
        project_b.mkdir()
        with self.assertRaises(LibraryError):
            fetch(self.root, project_a, "codex", ["alpha"], None, False)
        trust(self.root, rec["id"])
        first = fetch(self.root, project_a, "codex", ["alpha"], None, False)
        self.assertEqual(first["installed"][0]["status"], "installed")
        self.assertFalse((project_b / ".agents" / "skills" / "alpha").exists())
        second = fetch(self.root, project_a, "codex", ["alpha"], None, False)
        self.assertEqual(second["installed"][0]["status"], "already-installed")
        fetch(self.root, project_b, "claude", ["alpha"], None, False)
        self.assertTrue((project_b / ".claude" / "skills" / "alpha" / "SKILL.md").exists())
        (src / "SKILL.md").write_text("changed", encoding="utf-8")
        self.assertTrue((project_a / ".agents" / "skills" / "alpha" / "SKILL.md").exists())

    def test_archive_traversal_and_symlink(self):
        with self.assertRaises(LibraryError):
            safe_relative("a\\b")
        for name in ("../escape", "/absolute", "C:/windows"):
            data = io.BytesIO()
            with zipfile.ZipFile(data, "w") as z:
                z.writestr(name, "bad")
            with self.assertRaises(LibraryError, msg=name):
                extract_archive(data.getvalue(), self.base / "out")
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            info = zipfile.ZipInfo("link")
            info.external_attr = (0o120777 << 16)
            z.writestr(info, "target")
        with self.assertRaises(LibraryError):
            extract_archive(data.getvalue(), self.base / "out2")

    def test_bad_frontmatter_and_hash_change(self):
        src = make_skill(self.base / "src", "alpha")
        (src / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
        with self.assertRaises(LibraryError):
            add(self.root, str(src))
        self.assertEqual(read_records(self.root), [])
        src = make_skill(self.base / "other", "beta")
        add(self.root, str(src))
        rec = read_records(self.root)[0]
        (self.root / rec["path"] / "assets" / "data.bin").write_bytes(b"changed")
        with self.assertRaises(LibraryError):
            trust(self.root, rec["id"])
        self.assertFalse(doctor(self.root)["ok"])

    def test_search_fallback(self):
        src = make_skill(self.base / "src", "accessibility")
        add(self.root, str(src), "Wrong/Category")
        self.assertEqual(search(self.root, "accessibility")[0]["name"], "accessibility")


if __name__ == "__main__":
    unittest.main()
