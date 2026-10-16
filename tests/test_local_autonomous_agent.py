import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "local_autonomous_agent.py"
SPEC = importlib.util.spec_from_file_location("local_autonomous_agent", MODULE_PATH)
agent = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agent)


def diff_for(path, old="old", new="new"):
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        f"-{old}\n+{new}\n"
    )


class PatchValidationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_accepts_normal_source_patch(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "example.py").write_text("old\n", encoding="utf-8")
        agent.validate_patch(diff_for("src/example.py"), self.root)

    def test_rejects_empty_patch(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch("", self.root)

    def test_rejects_path_traversal(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for("../outside.py"), self.root)

    def test_rejects_workflow_changes(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for(".github/workflows/ci.yml"), self.root)

    def test_rejects_binary_artifact(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for("models/weights.safetensors"), self.root)

    def test_rejects_mismatched_diff_paths(self):
        patch = diff_for("src/a.py").replace("b/src/a.py", "b/src/b.py")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_rejects_non_standard_patch(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch("Here is your patch:\n" + diff_for("src/a.py"), self.root)


if __name__ == "__main__":
    unittest.main()
