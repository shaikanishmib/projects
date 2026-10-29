from pathlib import Path

import pytest

from sec_filing_intelligence.corpus import load_documents
from sec_filing_intelligence.retrieval import Index


@pytest.fixture
def fixture_dir():
    return Path(__file__).resolve().parents[1] / "data" / "fixtures"


@pytest.fixture
def documents(fixture_dir):
    return load_documents(fixture_dir / "filings.json")


@pytest.fixture
def index(documents):
    return Index(documents)
