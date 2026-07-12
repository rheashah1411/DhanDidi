import pytest

from document_reader import MAX_FILE_BYTES, clean_text, extract_text


def test_text_upload_and_cleanup() -> None:
    raw = "  Salary   Slip  \n\n Net Pay: Rs 42,000 \x00"
    result = clean_text(extract_text("salary.txt", raw.encode()))

    assert result == "Salary Slip\nNet Pay: Rs 42,000"


def test_rejects_unsupported_file() -> None:
    with pytest.raises(ValueError, match="unsupported-file"):
        extract_text("archive.zip", b"not a document")


def test_rejects_large_file_before_processing() -> None:
    with pytest.raises(ValueError, match="file-too-large"):
        extract_text("large.txt", b"x" * (MAX_FILE_BYTES + 1))
