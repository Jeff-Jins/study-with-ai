import tempfile
import unittest
from pathlib import Path

from grow_loader import grow


def write_note(root, rel, title, meta, body=""):
    d = root / "tree" / rel
    d.mkdir(parents=True)
    (d / "README.md").write_text(f"<!-- supervised: {meta} -->\n# {title}\n\n{body}", encoding="utf-8")
    return d


class TmpRootCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()


class ScanTest(TmpRootCase):
    def test_reads_notes_and_skips_plain_readmes(self):
        write_note(self.root, "CS/네트워크/2026-11-10-tcp", "TCP",
                   "status=done started=2026-11-10 done=2026-11-11")
        (self.root / "tree" / "CS" / "README.md").write_text("# 그냥 메모\n", encoding="utf-8")
        notes = grow.scan(self.root)
        self.assertEqual(len(notes), 1)
        n = notes[0]
        self.assertEqual(n.path, Path("tree/CS/네트워크/2026-11-10-tcp"))
        self.assertEqual(n.branch, ("CS", "네트워크"))
        self.assertEqual(n.title, "TCP")
        self.assertEqual(n.status, "done")
        self.assertEqual(n.started, "2026-11-10")
        self.assertEqual(n.done, "2026-11-11")

    def test_without_tree_dir(self):
        self.assertEqual(grow.scan(self.root), [])

    def test_skips_readme_inside_lab(self):
        d = write_note(self.root, "CS/2026-11-10-tcp", "TCP", "status=studying started=2026-11-10")
        lab = d / "lab"
        lab.mkdir()
        (lab / "README.md").write_text(
            "<!-- supervised: status=done started=2026-11-10 -->\n# 예제\n", encoding="utf-8")
        notes = grow.scan(self.root)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, "TCP")

    def test_skips_non_utf8_readme(self):
        write_note(self.root, "CS/2026-11-10-tcp", "TCP", "status=studying started=2026-11-10")
        bad = self.root / "tree" / "CS" / "README.md"
        bad.write_bytes(b"\xff\xfe\x00bad")
        self.assertEqual(len(grow.scan(self.root)), 1)


def sample_notes():
    N = grow.Note
    return [
        N(Path("tree/CS/네트워크/2026-11-10-tcp"), ("CS", "네트워크"), "TCP (기초) [1]", "done", "2026-11-10", "2026-11-11"),
        N(Path("tree/CS/운영체제/2026-11-12-proc"), ("CS", "운영체제"), "프로세스", "done", "2026-11-12", "2026-11-12"),
        N(Path("tree/영어/2026-11-13-word"), ("영어",), "단어 30개", "studying", "2026-11-13", None),
    ]


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.block = grow.render_block(sample_notes())

    def test_wrapped_in_markers(self):
        self.assertTrue(self.block.startswith(grow.START_MARK))
        self.assertTrue(self.block.endswith(grow.END_MARK))

    def test_stats_line(self):
        self.assertIn("> 🍃 잎 **2**개 · 🌱 공부 중 **1**개 · 📅 최근 공부 2026-11-13", self.block)

    def test_mindmap_structure(self):
        self.assertIn(
            "```mermaid\nmindmap\n  root((🌳 study-with-ai))\n"
            "    CS\n      네트워크\n        🍃 TCP 기초 1\n      운영체제\n        🍃 프로세스\n```",
            self.block,
        )

    def test_clickable_tree_under_mindmap(self):
        after = self.block.split("```mermaid")[1].split("```", 1)[1]
        tree = after.split("## 🌱 공부 중")[0]
        self.assertIn(
            "<details>\n<summary>🍃 잎 바로가기 (펼치기)</summary>\n\n<pre>\n"
            "🌳 study-with-ai\n"
            "└── CS\n"
            "    ├── 네트워크\n"
            '    │   └── 🍃 <a href="tree/CS/%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC/2026-11-10-tcp/README.md">TCP (기초) [1]</a> · 2026-11-11\n'
            "    └── 운영체제\n"
            '        └── 🍃 <a href="tree/CS/%EC%9A%B4%EC%98%81%EC%B2%B4%EC%A0%9C/2026-11-12-proc/README.md">프로세스</a> · 2026-11-12\n'
            "</pre>\n\n</details>\n",
            tree,
        )
        self.assertNotIn("단어", tree)

    def test_tree_escapes_html(self):
        N = grow.Note
        block = grow.render_block([N(Path("tree/a/2026-01-01-x"), ("a<b",), "x & <y>", "done", "2026-01-01", "2026-01-01")])
        self.assertIn("└── a&lt;b\n", block)
        self.assertIn(">x &amp; &lt;y&gt;</a>", block)

    def test_empty_tree_has_no_link_list(self):
        self.assertNotIn("<pre>", grow.render_block([]))

    def test_studying_not_in_mindmap_but_listed(self):
        mermaid = self.block.split("```mermaid")[1].split("```")[0]
        self.assertNotIn("단어", mermaid)
        self.assertIn(
            "- [단어 30개](tree/%EC%98%81%EC%96%B4/2026-11-13-word/README.md) · 영어 · 2026-11-13 시작",
            self.block,
        )

    def test_recent_table_newest_first(self):
        lines = self.block.splitlines()
        i = lines.index("| 날짜 | 가지 | 노트 |")
        self.assertTrue(lines[i + 2].startswith("| 2026-11-12 | CS / 운영체제 | [프로세스]("))
        self.assertTrue(lines[i + 3].startswith("| 2026-11-11 | CS / 네트워크 | [TCP (기초) \\[1\\]]("))

    def test_empty_tree(self):
        block = grow.render_block([])
        self.assertIn("  root((🌳 study-with-ai))\n```", block)
        self.assertIn("아직 잎이 없어요", block)
        self.assertIn("지금 공부 중인 노트가 없어요.", block)

    def test_mermaid_text_strips_shape_chars(self):
        self.assertEqual(grow.mermaid_text('a(b)[c]{d}"e"<f>`g`'), "abcdefg")
        self.assertEqual(grow.mermaid_text("  여러   칸  "), "여러 칸")
        self.assertEqual(grow.mermaid_text("()"), "?")


class UpdateReadmeTest(TmpRootCase):
    def read(self):
        return (self.root / "README.md").read_text(encoding="utf-8")

    def test_creates_with_header(self):
        grow.update_readme(self.root, [])
        text = self.read()
        self.assertTrue(text.startswith(grow.README_HEADER))
        self.assertIn(grow.START_MARK, text)
        self.assertTrue(text.endswith(grow.END_MARK + "\n"))

    def test_preserves_outside_markers(self):
        (self.root / "README.md").write_text(
            "# 내 제목\n\n머리말\n\n<!-- grow:start -->\n옛날 내용\n<!-- grow:end -->\n\n꼬리말\n",
            encoding="utf-8",
        )
        grow.update_readme(self.root, [])
        text = self.read()
        self.assertTrue(text.startswith("# 내 제목\n\n머리말\n\n<!-- grow:start -->"))
        self.assertTrue(text.endswith("<!-- grow:end -->\n\n꼬리말\n"))
        self.assertNotIn("옛날 내용", text)

    def test_appends_when_markers_missing_and_is_idempotent(self):
        (self.root / "README.md").write_text("# 손으로 쓴 README\n", encoding="utf-8")
        grow.update_readme(self.root, [])
        grow.update_readme(self.root, [])
        text = self.read()
        self.assertTrue(text.startswith("# 손으로 쓴 README\n\n<!-- grow:start -->"))
        self.assertEqual(text.count(grow.START_MARK), 1)

    def _assert_broken(self, content):
        path = self.root / "README.md"
        path.write_text(content, encoding="utf-8")
        with self.assertRaises(grow.GrowError):
            grow.update_readme(self.root, [])
        self.assertEqual(self.read(), content)

    def test_end_before_start_raises_and_leaves_file(self):
        self._assert_broken("앞\n<!-- grow:end -->\n중간\n<!-- grow:start -->\n뒤\n")

    def test_start_without_end_raises_and_leaves_file(self):
        self._assert_broken("앞\n<!-- grow:start -->\n사용자 글\n")

    def test_end_without_start_raises_and_leaves_file(self):
        self._assert_broken("앞\n<!-- grow:end -->\n")


if __name__ == "__main__":
    unittest.main()
