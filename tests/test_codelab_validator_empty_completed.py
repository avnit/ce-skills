import importlib.util
import json
import os
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

tester = _load(REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py")
validator = _load(REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py")

def test_crlf_command_extraction(tmp_path):
    md_content = "## Step 1\r\n```bash\r\necho hello-crlf\r\n```\r\n"
    md_file = tmp_path / "crlf_lab.md"
    md_file.write_bytes(md_content.encode('utf-8'))
    
    t = tester.StatefulCodelabTester(str(md_file))
    steps = t.parse_codelab()
    
    assert len(steps) == 1
    assert steps[0]["commands"] == ["echo hello-crlf"]

def test_different_fence_languages_extraction(tmp_path):
    md_content = (
        "## Step 1\n"
        "```sh\n"
        "echo sh-cmd\n"
        "```\n"
        "## Step 2\n"
        "```shell\n"
        "echo shell-cmd\n"
        "```\n"
        "## Step 3\n"
        "```console\n"
        "echo console-cmd\n"
        "```\n"
        "## Step 4\n"
        "```\n"
        "echo bare-cmd\n"
        "```\n"
    )
    md_file = tmp_path / "lang_lab.md"
    md_file.write_text(md_content, encoding='utf-8')
    
    t = tester.StatefulCodelabTester(str(md_file))
    steps = t.parse_codelab()
    
    assert len(steps) == 4
    assert steps[0]["commands"] == ["echo sh-cmd"]
    assert steps[1]["commands"] == ["echo shell-cmd"]
    assert steps[2]["commands"] == []  # console is non-executable
    assert steps[3]["commands"] == ["echo bare-cmd"]

def test_zero_commands_lab_fails(tmp_path, monkeypatch):
    md_content = "## Step 1\nJust prose text with no code blocks.\n"
    md_file = tmp_path / "zero_lab.md"
    md_file.write_text(md_content, encoding='utf-8')
    
    t = tester.StatefulCodelabTester(str(md_file))
    
    class MockRunner:
        def run_command(self, *args, **kwargs):
            return 0, ""
        def set_env(self, *args, **kwargs):
            pass
        def close(self):
            pass
            
    monkeypatch.setattr(tester, "SubshellRunner", lambda *args, **kwargs: MockRunner())
    
    success = t.run()
    assert success is False
    
    progress_file = os.path.join(t.tester_state_dir, "progress.json")
    assert os.path.exists(progress_file)
    with open(progress_file, "r") as f:
        progress = json.load(f)
    assert progress["status"] == "FAILED"

def test_validator_html_prettyprint_extraction(monkeypatch):
    html_content = (
        "<html>\n"
        "<head><title>My Test Lab</title></head>\n"
        "<body>\n"
        "<h2>Step 1: Create GCS Bucket</h2>\n"
        "<pre class=\"prettyprint\"><code>gcloud storage buckets create gs://my-bucket</code></pre>\n"
        "<h2>Step 2: Simple python script (not bash)</h2>\n"
        "<pre class=\"prettyprint\"><code>print('hello')</code></pre>\n"
        "</body>\n"
        "</html>\n"
    )
    
    class MockResponse:
        def read(self):
            return html_content.encode('utf-8')
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
            
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, *args, **kwargs: MockResponse())
    
    markdown_out = validator.download_url("http://example.com/test-lab")
    
    assert "gcloud storage buckets create gs://my-bucket" in markdown_out
    assert "print('hello')" not in markdown_out
    assert "```bash" in markdown_out

def test_crlf_raw_matching(monkeypatch):
    import io
    t = tester.StatefulCodelabTester("dummy.md")
    crlf_content = "## Step 1\r\n```bash\r\necho hello-crlf-raw\r\n```\r\n"
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: io.StringIO(crlf_content))
    steps = t.parse_codelab()
    assert len(steps) == 1
    assert steps[0]["commands"] == ["echo hello-crlf-raw"]

