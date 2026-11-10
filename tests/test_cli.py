import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from grow_loader import grow


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True).stdout


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.name", "Test")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "config", "commit.gpgsign", "false")
        self.today = grow.dt.date.today().isoformat()

    def tearDown(self):
        self.tmp.cleanup()

    def run_grow(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = grow.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def subjects(self):
        return git(self.root, "log", "--format=%s").splitlines()

    def note_dir(self):
        return self.root / "tree" / "CS" / "네트워크" / f"{self.today}-3-way-handshake"

    def start_note(self):
        code, _, err = self.run_grow("start", "CS/네트워크", "3-way handshake")
        self.assertEqual(code, 0, err)
        return self.note_dir()

    def add_todo(self, d, checked):
        readme = d / "README.md"
        mark = "x" if checked else " "
        readme.write_text(readme.read_text(encoding="utf-8")
                          + f"- [{mark}] tcpdump로 캡처\n  - 확인: [S] 보임\n", encoding="utf-8")

    def note_text(self):
        return (self.note_dir() / "README.md").read_text(encoding="utf-8")

    def root_readme(self):
        return (self.root / "README.md").read_text(encoding="utf-8")

    # ── start ──

    def test_start_creates_note_and_commits(self):
        self.start_note()
        text = self.note_text()
        self.assertTrue(text.startswith(
            f"<!-- supervised: status=studying started={self.today} -->\n"
            "# 3-way handshake\n\n> 가지: CS / 네트워크\n"))
        for h in ("## 개념 설명", "## 핵심 요약", "## 참고자료", "## TODO 실습"):
            self.assertIn(h, text)
        self.assertEqual(self.subjects(), ["🌱 start: CS / 네트워크 / 3-way handshake"])
        self.assertIn("[3-way handshake](", self.root_readme())

    def test_start_long_korean_title(self):
        title = "가나다라마바사아자차" * 10
        code, _, err = self.run_grow("start", "CS/네트워크", title)
        self.assertEqual(code, 0, err)
        names = [p.name for p in (self.root / "tree" / "CS" / "네트워크").iterdir()]
        self.assertEqual(len(names), 1)
        self.assertLessEqual(len(names[0].encode("utf-8")), 211)

    def test_start_same_note_twice_fails(self):
        self.start_note()
        code, _, err = self.run_grow("start", "CS/네트워크", "3-way handshake")
        self.assertEqual(code, 1)
        self.assertIn("이미 있는 노트", err)
        self.assertEqual(len(self.subjects()), 1)

    def test_start_rejects_escape(self):
        code, _, err = self.run_grow("start", "../밖", "x")
        self.assertEqual(code, 1)
        self.assertFalse((self.base / "밖").exists())

    # ── done ──

    def test_done_refuses_unchecked_todos(self):
        d = self.start_note()
        self.add_todo(d, checked=False)
        code, _, err = self.run_grow("done", str(d))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] tcpdump로 캡처", err)
        self.assertIn("status=studying", self.note_text())

    def test_done_with_force(self):
        d = self.start_note()
        self.add_todo(d, checked=False)
        code, _, err = self.run_grow("done", str(d), "--force")
        self.assertEqual(code, 0, err)
        self.assertIn("status=done", self.note_text())

    def test_done_grows_leaf_and_commits_without_remote(self):
        d = self.start_note()
        self.add_todo(d, checked=True)
        code, out, err = self.run_grow("done", str(d.relative_to(self.root)))
        self.assertEqual(code, 0, err)
        self.assertIn("remote가 없어 push를 건너뜁니다", out)
        self.assertIn("총 1개", out)
        self.assertIn(f"status=done started={self.today} done={self.today}", self.note_text())
        readme = self.root_readme()
        self.assertIn("🍃 3-way handshake", readme)
        self.assertIn("지금 공부 중인 노트가 없어요.", readme)
        self.assertEqual(self.subjects()[0], "🍃 grow: CS / 네트워크 / 3-way handshake")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_done_accepts_tree_relative_readme_path(self):
        self.start_note()
        code, _, err = self.run_grow("done", f"CS/네트워크/{self.today}-3-way-handshake/README.md")
        self.assertEqual(code, 0, err)

    def test_done_twice_fails(self):
        d = self.start_note()
        self.run_grow("done", str(d))
        code, _, err = self.run_grow("done", str(d))
        self.assertEqual(code, 1)
        self.assertIn("이미 완료", err)

    def test_done_unknown_note_fails(self):
        code, _, err = self.run_grow("done", "없는/노트")
        self.assertEqual(code, 1)
        self.assertIn("노트를 찾을 수 없습니다", err)

    def test_done_pushes_to_remote(self):
        bare = self.base / "remote.git"
        git(self.base, "init", "-q", "--bare", str(bare))
        git(self.root, "remote", "add", "origin", str(bare))
        d = self.start_note()
        code, _, err = self.run_grow("done", str(d))
        self.assertEqual(code, 0, err)
        self.assertEqual(git(bare, "log", "--format=%s", "main").splitlines()[0],
                         "🍃 grow: CS / 네트워크 / 3-way handshake")

    def test_push_failure_keeps_commit(self):
        git(self.root, "remote", "add", "origin", str(self.base / "nope.git"))
        d = self.start_note()
        code, _, err = self.run_grow("done", str(d))
        self.assertEqual(code, 0)
        self.assertIn("push 실패", err)
        self.assertTrue(self.subjects()[0].startswith("🍃 grow:"))

    # ── list / refresh ──

    def test_list_shows_studying(self):
        self.start_note()
        code, out, _ = self.run_grow("list")
        self.assertEqual(code, 0)
        self.assertIn(f"tree/CS/네트워크/{self.today}-3-way-handshake", out)
        self.assertIn("3-way handshake", out)

    def test_refresh_writes_readme(self):
        code, out, _ = self.run_grow("refresh")
        self.assertEqual(code, 0)
        self.assertIn(grow.START_MARK, self.root_readme())


if __name__ == "__main__":
    unittest.main()
