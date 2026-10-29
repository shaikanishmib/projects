"""Opt-in acquisition of one manually selected public SEC filing. Never runs on import."""

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .corpus import digest


MAX_BYTES = 15_000_000


def validate_url(url: str) -> str:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "www.sec.gov"
            or parts.query or parts.fragment
            or not re.fullmatch(r"/Archives/edgar/data/[0-9]+/[0-9]{18}/[A-Za-z0-9_-]+\.(?:htm|html|txt)", parts.path)):
        raise ValueError("Use a direct https://www.sec.gov/Archives/edgar/data/CIK/ACCESSION/document.htm URL")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused; select a direct SEC filing URL")


class FilingHTML(HTMLParser):
    """Basic visible-text extraction, not a complete financial-table parser."""
    BLOCKS = {"p", "div", "br", "tr", "table", "h1", "h2", "h3", "li"}
    HIDDEN = {"script", "style", "head", "ix:hidden"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self.hidden_depth += 1
        if not self.hidden_depth:
            if tag in self.BLOCKS:
                self.parts.append("\n\n")
            elif tag in {"td", "th"}:
                self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.HIDDEN and self.hidden_depth:
            self.hidden_depth -= 1
        if not self.hidden_depth and tag in self.BLOCKS:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


def normalize(raw: str, html: bool) -> str:
    if html:
        parser = FilingHTML()
        parser.feed(raw)
        parser.close()
        raw = "".join(parser.parts)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in raw.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def acquire(url: str, user_agent: str, document_id: str, company: str, form: str,
            period: str, output: Path) -> Path:
    validate_url(url)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", document_id):
        raise ValueError("Invalid document ID")
    if not all(value.strip() for value in (company, form, period)):
        raise ValueError("Company, form, and period are required")
    if "@" not in user_agent or len(user_agent) < 12 or any(c in user_agent for c in "\r\n"):
        raise ValueError("Supply an identifying user agent with organization and contact email")
    output.mkdir(parents=True, exist_ok=True)
    bundle = output / document_id
    if bundle.exists():
        raise ValueError("Output bundle already exists; choose a new document ID or output directory")
    # One request, no retries, no fan-out. Pause even for repeated serial invocations.
    time.sleep(0.2)
    request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"
    if len(raw) > MAX_BYTES:
        raise ValueError("Filing exceeds the 15 MB download limit")
    if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
        raise ValueError(f"Unexpected content type: {content_type}")
    decoded = raw.decode(charset, errors="strict")
    text = normalize(decoded, html=content_type != "text/plain")
    if not text:
        raise ValueError("Filing contains no extracted text")
    doc = {"id": document_id, "company": company, "form": form, "period": period,
           "source_url": url,
           "provenance": "Public SEC EDGAR filing; normalized locally; see adjacent manifest.json.",
           "text": text}
    import hashlib
    manifest = {"source_url": url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "raw_sha256": hashlib.sha256(raw).hexdigest(), "normalized_sha256": digest(text),
                "raw_bytes": len(raw), "content_type": content_type, "charset": charset,
                "normalizer_version": "1", "metadata_origin": "User-supplied; verify against filing header",
                "rights": "Publicly accessible SEC filing; issuer/exhibit rights require separate review."}
    # Create the bundle only after a complete, validated response. Never store contact info.
    bundle.mkdir(exist_ok=False)
    (bundle / "raw.bin").write_bytes(raw)
    (bundle / "corpus.json").write_text(json.dumps([doc], indent=2) + "\n", encoding="utf-8")
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return bundle / "corpus.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--form", choices=["10-K", "10-Q"], required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--output", type=Path, default=Path("data/downloads"))
    args = parser.parse_args()
    try:
        print(acquire(args.url, args.user_agent, args.document_id, args.company,
                      args.form, args.period, args.output))
    except (OSError, URLError, ValueError, LookupError) as exc:
        parser.exit(2, f"Acquisition failed (no automatic retry): {exc}\n")


if __name__ == "__main__":
    main()
