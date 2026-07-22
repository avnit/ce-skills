import inspect
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "scripts"
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from bug_to_lesson_processor import (  # noqa: E402
    GcloudUserCredentials,
    _redact,
)


def test_redact_account_identifier():
    """Verify _redact properly masks email local-parts."""
    assert _redact("someuser@google.com") == "som***@google.com"
    assert _redact("ab@google.com") == "ab***@google.com"
    assert _redact("user") == "use***"
    assert _redact("") == "***"
    assert _redact(None) == "***"


def test_logging_calls_use_redacted_account():
    """Verify all logging format strings in GcloudUserCredentials.refresh use _redact(self.account)."""
    source = inspect.getsource(GcloudUserCredentials.refresh)

    # Grep-style assertions: check _redact is called for logged account references
    assert "_redact(self.account)" in source
    assert "logging.info(f\"Refreshing gcloud access token for account {_redact(self.account)}...\")" in source
    assert "logging.info(f\"Successfully refreshed token for {_redact(self.account)} (cached for 55 minutes).\")" in source
    assert "logging.error(f\"Failed to fetch access token via gcloud for {_redact(self.account)}: {e}\")" in source

    # Ensure unredacted self.account is not logged clear-text
    assert "logging.info(f\"Refreshing gcloud access token for account {self.account}...\")" not in source
    assert "logging.info(f\"Successfully refreshed token for {self.account}" not in source
    assert "logging.error(f\"Failed to fetch access token via gcloud for {self.account}" not in source
