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
    """Verify logging calls contain no account expressions and RuntimeError retains _redact(self.account)."""
    source = inspect.getsource(GcloudUserCredentials.refresh)

    # Constant log message assertions
    assert 'logging.info("Refreshing gcloud access token for the configured closed-loop account...")' in source
    assert 'logging.info("Successfully refreshed access token (cached for 55 minutes).")' in source
    assert 'logging.error(f"Failed to fetch access token via gcloud: {e}")' in source

    # Assert no logging line in refresh contains self.account (directly or via _redact)
    for line in source.splitlines():
        if "logging." in line:
            assert "self.account" not in line

    # Assert RuntimeError line retains _redact(self.account)
    assert 'raise RuntimeError(f"Authentication failed for {_redact(self.account)}: {e}") from e' in source
