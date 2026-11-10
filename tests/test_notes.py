import unittest

from grow_loader import grow


class SlugifyTest(unittest.TestCase):
    def test_spaces_become_hyphens(self):
        self.assertEqual(grow.slugify("3-way handshake"), "3-way-handshake")

    def test_korean_kept_forbidden_removed(self):
        self.assertEqual(grow.slugify("TCP/IP 기초: 정리?"), "TCPIP-기초-정리")

    def test_collapses_repeated_hyphens(self):
        self.assertEqual(grow.slugify("  a  -  b  "), "a-b")

    def test_empty_raises(self):
        with self.assertRaises(grow.GrowError):
            grow.slugify(" /?: ")


class ParseBranchTest(unittest.TestCase):
    def test_split_and_trim(self):
        self.assertEqual(grow.parse_branch(" CS / 네트워크 /TCP/ "), ("CS", "네트워크", "TCP"))

    def test_backslash_also_splits(self):
        self.assertEqual(grow.parse_branch("CS\\OS"), ("CS", "OS"))

    def test_dotdot_rejected(self):
        with self.assertRaises(grow.GrowError):
            grow.parse_branch("CS/../etc")

    def test_empty_rejected(self):
        with self.assertRaises(grow.GrowError):
            grow.parse_branch(" / ")


class MetaTest(unittest.TestCase):
    TEXT = "<!-- supervised: status=studying started=2026-11-10 -->\n# T\n"

    def test_parse(self):
        self.assertEqual(grow.parse_meta(self.TEXT), {"status": "studying", "started": "2026-11-10"})

    def test_parse_missing(self):
        self.assertEqual(grow.parse_meta("# T\n"), {})

    def test_set_replaces_existing(self):
        out = grow.set_meta(self.TEXT, {"status": "done", "started": "2026-11-10", "done": "2026-11-11"})
        self.assertEqual(out, "<!-- supervised: status=done started=2026-11-10 done=2026-11-11 -->\n# T\n")

    def test_set_prepends_when_missing(self):
        out = grow.set_meta("# T\n", {"status": "studying"})
        self.assertEqual(out, "<!-- supervised: status=studying -->\n# T\n")


class TextHelpersTest(unittest.TestCase):
    def test_unchecked_todos(self):
        text = (
            "## TODO 실습\n"
            "- [x] 첫째\n"
            "- [ ] 둘째\n"
            "  - 확인: ok\n"
            "- [X] 셋째\n"
            "  * [ ] 넷째\n"
        )
        self.assertEqual(grow.unchecked_todos(text), ["둘째", "넷째"])

    def test_title_of(self):
        self.assertEqual(grow.title_of("<!-- x -->\n# 제목 \n## 소제목\n", "fb"), "제목")
        self.assertEqual(grow.title_of("내용만\n", "fb"), "fb")


if __name__ == "__main__":
    unittest.main()
