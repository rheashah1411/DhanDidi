"""Safe text extraction for DhanDidi's supported upload formats."""

from __future__ import annotations

import io
from pathlib import Path

MAX_FILE_BYTES = 20 * 1024 * 1024


def _ocr_pil_image(image) -> str:
    import pytesseract  # type: ignore
    from PIL import ImageEnhance, ImageFilter, ImageOps  # type: ignore

    image = ImageOps.exif_transpose(image).convert("L")
    image.thumbnail((2400, 2400))
    image = ImageEnhance.Contrast(image).enhance(1.7).filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(image, config="--psm 6")


def _read_pdf(data: bytes) -> str:
    text_parts: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(data))
        text_parts = [(page.extract_text() or "") for page in reader.pages]
    except Exception:
        pass
    text = "\n".join(text_parts).strip()
    if len(text) >= 80:
        return text

    # Scanned PDFs need OCR. Rendering is capped to avoid excessive memory use.
    try:
        import fitz  # type: ignore
        from PIL import Image  # type: ignore

        document = fitz.open(stream=data, filetype="pdf")
        pages: list[str] = []
        for page in list(document)[:12]:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            pages.append(_ocr_pil_image(image))
        return "\n".join(pages)
    except Exception:
        return text


def extract_text(filename: str, data: bytes) -> str:
    """Extract text without writing the user's uploaded document to disk."""
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("file-too-large")
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".csv"}:
        for encoding in ("utf-8-sig", "utf-16", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
    if suffix == ".pdf":
        return _read_pdf(data)
    if suffix in {".png", ".jpg", ".jpeg"}:
        from PIL import Image  # type: ignore

        with Image.open(io.BytesIO(data)) as image:
            return _ocr_pil_image(image)
    raise ValueError("unsupported-file")


def clean_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", " ").splitlines()]
    return "\n".join(line for line in lines if line).strip()
