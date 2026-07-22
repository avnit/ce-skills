import importlib.util
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

validator = _load(REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py")

def test_script_style_elements_excluded(monkeypatch):
    """HTML with <script>alert(1)</script> + a <style> block -> neither in the output."""
    html_content = (
        "<html>\n"
        "<head>\n"
        "<title>Script and Style Test</title>\n"
        "<style>body { color: red; }</style>\n"
        "<script>console.log('injected script');</script>\n"
        "</head>\n"
        "<body>\n"
        "<h1>My Header</h1>\n"
        "<pre class=\"language-bash\"><code>gcloud info</code></pre>\n"
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
    
    markdown_out = validator.download_url("http://example.com/test")
    
    # Assert injected script/style contents are not in output
    assert "color: red" not in markdown_out
    assert "console.log" not in markdown_out
    assert "injected script" not in markdown_out
    
    # Assert header and bash code are preserved
    assert "# My Header" in markdown_out
    assert "gcloud info" in markdown_out

def test_malformed_spaced_script_tags_excluded(monkeypatch):
    """A malformed/spaced tag (e.g. <script >...</script >) -> content still excluded."""
    html_content = (
        "<html>\n"
        "<body>\n"
        "<script  type=\"text/javascript\" >\n"
        "alert(1);\n"
        "</script >\n"
        "<style   >\n"
        "h1 { display: none; }\n"
        "</style  >\n"
        "<h2>Header 2</h2>\n"
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
    
    markdown_out = validator.download_url("http://example.com/test")
    
    assert "alert(1)" not in markdown_out
    assert "display: none" not in markdown_out
    assert "## Header 2" in markdown_out

def test_html_entity_decoding(monkeypatch):
    """Verifies that entity decoding works via html.unescape."""
    html_content = (
        "<html>\n"
        "<body>\n"
        "<pre class=\"language-bash\"><code>echo &quot;hello&quot; &amp;&amp; cat &lt;/dev/null &gt;/dev/null</code></pre>\n"
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
    
    markdown_out = validator.download_url("http://example.com/test")
    
    assert 'echo "hello" && cat </dev/null >/dev/null' in markdown_out
