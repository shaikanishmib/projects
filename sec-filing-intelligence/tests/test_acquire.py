import json

import pytest

from sec_filing_intelligence import acquire
from sec_filing_intelligence.corpus import load_documents


VALID_URL = "https://www.sec.gov/Archives/edgar/data/123456/000012345624000001/report.htm"


@pytest.mark.parametrize("url", [
    "http://www.sec.gov/Archives/edgar/data/1/000012345624000001/report.htm",
    "https://www.sec.gov.attacker.invalid/Archives/edgar/data/1/000012345624000001/report.htm",
    "https://www.sec.gov/Archives/edgar/data/1/000012345624000001/../report.htm",
    VALID_URL + "?redirect=evil",
    "https://user@www.sec.gov/Archives/edgar/data/1/000012345624000001/report.htm",
])
def test_url_restrictions(url):
    with pytest.raises(ValueError):
        acquire.validate_url(url)


def test_visible_text_normalization():
    html = "<head><title>hidden</title></head><p>Revenue &amp; cash</p><script>attack()</script><table><tr><td>2024</td><td>120</td></tr></table>"
    text = acquire.normalize(html, html=True)
    assert "Revenue & cash" in text
    assert "2024 | 120" in text
    assert "hidden" not in text
    assert "attack()" not in text


def test_download_with_mocked_transport(monkeypatch, tmp_path):
    from email.message import Message
    from io import BytesIO

    response = BytesIO(b"<p>Example revenue 120 million.</p>")
    response.headers = Message()
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    seen = []

    class MockOpener:
        def open(self, request, timeout):
            seen.append(request.full_url)
            assert timeout == 30
            return response

    monkeypatch.setattr(acquire, "build_opener", lambda *args: MockOpener())
    monkeypatch.setattr(acquire.time, "sleep", lambda seconds: None)
    path = acquire.acquire(VALID_URL, "Teaching contact@example.invalid", "example", "Example",
                           "10-K", "2024-12-31", tmp_path)
    assert seen == [VALID_URL]
    assert load_documents(path)[0].text == "Example revenue 120 million."
    manifest = json.loads((path.parent / "manifest.json").read_text())
    assert len(manifest["raw_sha256"]) == 64
    assert "contact@example.invalid" not in json.dumps(manifest)
    with pytest.raises(ValueError, match="already exists"):
        acquire.acquire(VALID_URL, "Teaching contact@example.invalid", "example", "Example",
                        "10-K", "2024-12-31", tmp_path)
    assert len(seen) == 1


def test_redirects_rejected():
    with pytest.raises(ValueError, match="Redirect"):
        acquire.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://attacker.invalid")
