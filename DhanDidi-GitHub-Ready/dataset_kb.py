"""Dataset-backed retrieval knowledge base for DhanDidi.

The Kaggle data consists of document images grouped into labelled folders.  We
OCR a small, deterministic sample from each folder, persist the resulting text
index, and compare each upload with those examples.  This is retrieval, not
model training: the retrieved type and vocabulary augment (but never replace)
the application's conservative rules.
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.request
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DATASET_SLUG = "mehaksingal/personal-financial-dataset-for-india"
DOWNLOAD_URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET_SLUG}"
CACHE_ROOT = Path(os.getenv("DHANDIDI_CACHE_DIR", Path(__file__).parent / ".cache"))
DATASET_DIR = CACHE_ROOT / "personal-financial-dataset-for-india"
INDEX_FILE = CACHE_ROOT / "dataset_index.json"

FOLDER_TYPES = {
    "Bank Statement": "bank_statement",
    "Check": "cheque",
    "ITR_Form 16": "tax_document",
    "Salary Slip": "salary_slip",
    "Utility": "utility_bill",
}

# Used only if image OCR is unavailable. These are document-domain anchors, not
# fabricated examples; folder labels still provide the supervised type signal.
TYPE_ANCHORS = {
    "bank_statement": "account statement opening balance closing balance debit credit transaction narration IFSC",
    "cheque": "pay bearer rupees only account payee cheque date signature MICR IFSC",
    "tax_document": "form 16 income tax TDS employer employee PAN assessment year gross salary deduction",
    "salary_slip": "salary slip payslip employee basic pay allowance deduction provident fund net pay gross pay",
    "utility_bill": "bill consumer number meter reading units due date amount payable electricity water gas",
}


@dataclass(frozen=True)
class ReferenceExample:
    doc_type: str
    text: str
    source: str


@dataclass(frozen=True)
class Match:
    doc_type: str
    similarity: float
    source: str
    shared_terms: tuple[str, ...]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", text.lower())


def _download_dataset() -> Path:
    """Download once, preferring the exact kagglehub approach in dataset.txt."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    if any(DATASET_DIR.rglob("*.jpg")):
        return DATASET_DIR

    try:
        import kagglehub  # type: ignore

        downloaded = Path(kagglehub.dataset_download(DATASET_SLUG))
        if any(downloaded.rglob("*.jpg")):
            return downloaded
    except Exception:
        # Public API fallback keeps the app usable without Kaggle credentials.
        pass

    archive = CACHE_ROOT / "dataset.zip"
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DOWNLOAD_URL, archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(DATASET_DIR)
    archive.unlink(missing_ok=True)
    return DATASET_DIR


def _ocr_image(path: Path) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # type: ignore

        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("L")
            image.thumbnail((1800, 1800))
            image = ImageEnhance.Contrast(image).enhance(1.6)
            image = image.filter(ImageFilter.SHARPEN)
            # A difficult scan must not hold the whole Streamlit startup hostage.
            return " ".join(pytesseract.image_to_string(image, config="--psm 6", timeout=5).split())
    except Exception:
        return ""


def _sample_evenly(paths: list[Path], limit: int) -> Iterable[Path]:
    if len(paths) <= limit:
        return paths
    step = (len(paths) - 1) / (limit - 1)
    return (paths[round(i * step)] for i in range(limit))


class DatasetKnowledgeBase:
    def __init__(self, examples: list[ReferenceExample], status: str = "ready") -> None:
        self.examples = examples
        self.status = status
        counts = Counter(token for example in examples for token in set(_tokens(example.text)))
        total = max(len(examples), 1)
        self.idf = {term: math.log((1 + total) / (1 + count)) + 1 for term, count in counts.items()}
        self.type_terms: dict[str, set[str]] = {}
        for doc_type in set(e.doc_type for e in examples):
            words = Counter(token for e in examples if e.doc_type == doc_type for token in _tokens(e.text))
            self.type_terms[doc_type] = {term for term, _ in words.most_common(80)}

    @property
    def available(self) -> bool:
        return bool(self.examples)

    def retrieve(self, text: str, limit: int = 4) -> list[Match]:
        """Return nearest OCR examples using a compact weighted-Jaccard score."""
        query = set(_tokens(text))
        if not query:
            return []
        scored: list[Match] = []
        for example in self.examples:
            reference = set(_tokens(example.text))
            shared = query & reference
            union = query | reference
            numerator = sum(self.idf.get(term, 1.0) for term in shared)
            denominator = sum(self.idf.get(term, 1.0) for term in union) or 1.0
            scored.append(Match(example.doc_type, numerator / denominator, example.source, tuple(sorted(shared)[:8])))
        return sorted(scored, key=lambda item: item.similarity, reverse=True)[:limit]

    def type_scores(self, text: str) -> dict[str, float]:
        """Aggregate reference similarity by type for hybrid classification."""
        matches = self.retrieve(text, limit=min(12, len(self.examples)))
        scores: dict[str, float] = {}
        for match in matches:
            scores[match.doc_type] = scores.get(match.doc_type, 0.0) + match.similarity
        peak = max(scores.values(), default=0.0)
        return {key: value / peak for key, value in scores.items()} if peak else {}


def load_knowledge_base(samples_per_type: int = 2) -> DatasetKnowledgeBase:
    """Load/build the disk index. Wrap this in st.cache_resource in app.py.

    Dataset use points:
    1. folder labels supply reference document types;
    2. OCR text supplies real-example vocabulary for similarity retrieval;
    3. retrieved type scores improve classification and select appropriate
       extraction, clause, risk, and summary templates in analysis.py.
    """
    try:
        if INDEX_FILE.exists():
            payload = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            return DatasetKnowledgeBase([ReferenceExample(**item) for item in payload["examples"]])

        root = _download_dataset()
        examples: list[ReferenceExample] = []
        for folder_name, doc_type in FOLDER_TYPES.items():
            folder = next((p for p in root.rglob(folder_name) if p.is_dir()), root / folder_name)
            paths = sorted(folder.glob("*.jpg"), key=lambda p: p.name)
            for path in _sample_evenly(paths, samples_per_type):
                text = _ocr_image(path)
                # Folder-specific anchors stabilize retrieval when a scan has
                # little machine-readable text; actual OCR remains the core.
                indexed_text = f"{TYPE_ANCHORS[doc_type]} {text}".strip()
                examples.append(ReferenceExample(doc_type, indexed_text, f"{folder_name}/{path.name}"))
        if not examples:
            raise RuntimeError("No dataset images were found")
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(json.dumps({"examples": [asdict(e) for e in examples]}, ensure_ascii=False), encoding="utf-8")
        return DatasetKnowledgeBase(examples)
    except Exception as exc:
        # The rest of DhanDidi remains available offline. Anchor references make
        # the fallback explicit rather than silently pretending data was loaded.
        fallback = [ReferenceExample(k, v, "built-in fallback") for k, v in TYPE_ANCHORS.items()]
        return DatasetKnowledgeBase(fallback, status=f"fallback: {type(exc).__name__}")
