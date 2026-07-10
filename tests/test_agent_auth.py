import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


agent_auth = _load(REPO / "scripts" / "check_agent_auth.py", "check_agent_auth")


class TestAgentAuth(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="agent_auth_")
        self.allowlist = os.path.join(self.tmp, "agent-allowlist.json")
        with open(self.allowlist, "w", encoding="utf-8") as f:
            json.dump({"allowed": ["shacharbob"]}, f)

    def test_allowed_roles(self):
        for assoc in ("OWNER", "MEMBER", "COLLABORATOR"):
            self.assertTrue(agent_auth.is_authorized("shacharbob", assoc, self.allowlist))

    def test_unknown_author_denied(self):
        self.assertFalse(agent_auth.is_authorized("drive-by-account", "OWNER", self.allowlist))

    def test_weak_association_denied(self):
        for assoc in ("CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "NONE", ""):
            self.assertFalse(agent_auth.is_authorized("shacharbob", assoc, self.allowlist))

    def test_missing_allowlist_fails_closed(self):
        self.assertFalse(agent_auth.is_authorized("shacharbob", "OWNER", self.allowlist + ".missing"))

    def test_malformed_allowlist_fails_closed(self):
        with open(self.allowlist, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertFalse(agent_auth.is_authorized("shacharbob", "OWNER", self.allowlist))


if __name__ == "__main__":
    unittest.main()
