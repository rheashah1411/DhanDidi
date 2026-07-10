from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Any

import streamlit as st


APP_NAME = "DhanDidi"
SUPPORTED_LANGUAGES = ("en", "hi", "mr")


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "language_name": "English",
        "title": "DhanDidi",
        "subtitle": "An AI-powered financial document simplifier for women entering the formal banking system.",
        "description": "Upload a bank statement, loan agreement, policy page, or scheme form. DhanDidi extracts text, explains key details in plain language, and flags items worth checking.",
        "language_label": "Choose language",
        "uploader_label": "Upload a document",
        "sample_button": "Use sample document",
        "analyze_button": "Analyze document",
        "ready_to_analyze": "Document selected. Click Analyze document when you are ready.",
        "disclaimer": "DhanDidi is for information and education only. It is not legal, banking, or financial advice. For important decisions, verify with your bank, an authorized advisor, or the official scheme office.",
        "upload_help": "Supported files: PDF, PNG, JPG, JPEG, TXT, CSV",
        "sample_loaded": "Sample document loaded.",
        "no_document": "Upload a document or use the sample to begin.",
        "analysis_ready": "Analysis complete.",
        "analysis_warning": "I could only read part of this document. Please verify important details manually.",
        "extracted_text": "Extracted text",
        "key_details": "Key details",
        "simple_explanation": "Simple explanation",
        "risk_flags": "Risk flags",
        "high_risk": "High-risk clauses to review",
        "next_steps": "Suggested next steps",
        "confidence": "Confidence notes",
        "download_text": "Download extracted text",
        "download_summary": "Download summary report",
        "no_text": "I could not extract readable text from this file.",
        "ocr_missing": "OCR is not available in this environment. Text-based PDFs and TXT files will still work, but scanned images may not.",
        "amounts": "Money amounts",
        "dates": "Dates",
        "possible_period": "Possible statement period",
        "opening_balance": "Possible opening balance",
        "closing_balance": "Possible closing balance",
        "account_number": "Possible account number",
        "not_found": "Not found",
        "good_confidence": "The document had readable text and the app found dates or money amounts.",
        "medium_confidence": "The app found some text, but important details may be missing.",
        "low_confidence": "The app found very little readable text. Try a clearer image or a text-based PDF.",
        "summary_intro": "This appears to be a financial document showing money-related activity, obligations, or terms.",
        "summary_use": "You can use it to check payments, track balances, understand charges, and notice terms that need a second look.",
        "no_risks": "No strong warning sign was detected, but unknown payments or clauses should still be checked.",
        "terms_heading": "What this means in simple words",
    },
    "hi": {
        "language_name": "Hindi",
        "title": "धनदीदी",
        "subtitle": "पहली बार बैंकिंग सिस्टम में आने वाली महिलाओं के लिए AI financial document simplifier.",
        "description": "Bank statement, loan agreement, policy page या scheme form upload करें। धनदीदी text पढ़कर जरूरी बातें सरल भाषा में समझाती है और ध्यान देने वाली बातों को flag करती है।",
        "language_label": "भाषा चुनें",
        "uploader_label": "दस्तावेज़ अपलोड करें",
        "sample_button": "Sample document इस्तेमाल करें",
        "analyze_button": "दस्तावेज़ समझें",
        "ready_to_analyze": "Document selected है। Ready होने पर दस्तावेज़ समझें पर click करें।",
        "disclaimer": "धनदीदी सिर्फ जानकारी और शिक्षा के लिए है। यह legal, banking या financial advice नहीं है। जरूरी फैसलों के लिए अपने bank, authorized advisor या official scheme office से verify करें।",
        "upload_help": "Supported files: PDF, PNG, JPG, JPEG, TXT, CSV",
        "sample_loaded": "Sample document load हो गया।",
        "no_document": "शुरू करने के लिए document upload करें या sample इस्तेमाल करें।",
        "analysis_ready": "Analysis पूरा हुआ।",
        "analysis_warning": "मैं इस document का केवल कुछ हिस्सा पढ़ पाई। जरूरी details manually verify करें।",
        "extracted_text": "निकाला गया text",
        "key_details": "मुख्य जानकारी",
        "simple_explanation": "सरल explanation",
        "risk_flags": "Risk flags",
        "high_risk": "ध्यान से पढ़ने वाली high-risk बातें",
        "next_steps": "अगले कदम",
        "confidence": "Confidence notes",
        "download_text": "Extracted text download करें",
        "download_summary": "Summary report download करें",
        "no_text": "मैं इस file से readable text नहीं निकाल पाई।",
        "ocr_missing": "इस environment में OCR available नहीं है। Text-based PDFs और TXT files चलेंगी, लेकिन scanned images शायद न पढ़ें।",
        "amounts": "पैसों की amounts",
        "dates": "Dates",
        "possible_period": "संभावित statement period",
        "opening_balance": "संभावित opening balance",
        "closing_balance": "संभावित closing balance",
        "account_number": "संभावित account number",
        "not_found": "नहीं मिला",
        "good_confidence": "Document readable था और app को dates या money amounts मिले।",
        "medium_confidence": "कुछ text मिला, लेकिन जरूरी details missing हो सकती हैं।",
        "low_confidence": "बहुत कम readable text मिला। Clear image या text-based PDF try करें।",
        "summary_intro": "यह एक financial document लगता है जिसमें पैसों की activity, obligation या terms हैं।",
        "summary_use": "आप इसका उपयोग payments check करने, balance track करने, charges समझने और important terms देखने के लिए कर सकती हैं।",
        "no_risks": "कोई बहुत strong warning sign नहीं मिला, लेकिन unknown payments या clauses जरूर check करें।",
        "terms_heading": "इन शब्दों का आसान मतलब",
    },
    "mr": {
        "language_name": "Marathi",
        "title": "धनदीदी",
        "subtitle": "Formal banking system मध्ये येणाऱ्या महिलांसाठी AI financial document simplifier.",
        "description": "Bank statement, loan agreement, policy page किंवा scheme form upload करा. धनदीदी text वाचून महत्वाच्या गोष्टी सोप्या भाषेत सांगते आणि तपासायच्या गोष्टी flag करते.",
        "language_label": "भाषा निवडा",
        "uploader_label": "दस्तऐवज अपलोड करा",
        "sample_button": "Sample document वापरा",
        "analyze_button": "दस्तऐवज समजून घ्या",
        "ready_to_analyze": "Document selected आहे. Ready झाल्यावर दस्तऐवज समजून घ्या वर click करा.",
        "disclaimer": "धनदीदी फक्त माहिती आणि शिक्षणासाठी आहे. हे legal, banking किंवा financial advice नाही. महत्वाच्या निर्णयांसाठी bank, authorized advisor किंवा official scheme office कडून verify करा.",
        "upload_help": "Supported files: PDF, PNG, JPG, JPEG, TXT, CSV",
        "sample_loaded": "Sample document load झाले.",
        "no_document": "सुरू करण्यासाठी document upload करा किंवा sample वापरा.",
        "analysis_ready": "Analysis पूर्ण झाले.",
        "analysis_warning": "मी या document चा काही भागच वाचू शकले. महत्वाच्या details manually verify करा.",
        "extracted_text": "काढलेला text",
        "key_details": "मुख्य माहिती",
        "simple_explanation": "सोपी explanation",
        "risk_flags": "Risk flags",
        "high_risk": "काळजीपूर्वक वाचायच्या high-risk गोष्टी",
        "next_steps": "पुढचे steps",
        "confidence": "Confidence notes",
        "download_text": "Extracted text download करा",
        "download_summary": "Summary report download करा",
        "no_text": "मी या file मधून readable text काढू शकले नाही.",
        "ocr_missing": "या environment मध्ये OCR available नाही. Text-based PDFs आणि TXT files चालतील, पण scanned images कदाचित वाचता येणार नाहीत.",
        "amounts": "पैशांच्या amounts",
        "dates": "Dates",
        "possible_period": "संभाव्य statement period",
        "opening_balance": "संभाव्य opening balance",
        "closing_balance": "संभाव्य closing balance",
        "account_number": "संभाव्य account number",
        "not_found": "सापडले नाही",
        "good_confidence": "Document readable होते आणि app ला dates किंवा money amounts सापडले.",
        "medium_confidence": "काही text मिळाले, पण महत्वाच्या details missing असू शकतात.",
        "low_confidence": "खूप कमी readable text मिळाले. Clear image किंवा text-based PDF try करा.",
        "summary_intro": "हा financial document वाटतो ज्यात पैशांची activity, obligations किंवा terms आहेत.",
        "summary_use": "Payments check करणे, balance track करणे, charges समजणे आणि important terms पाहणे यासाठी याचा उपयोग होऊ शकतो.",
        "no_risks": "खूप strong warning sign दिसला नाही, पण unknown payments किंवा clauses नक्की check करा.",
        "terms_heading": "या शब्दांचा सोपा अर्थ",
    },
}


TERM_RULES: dict[str, dict[str, Any]] = {
    "emi": {
        "patterns": [r"\bemi\b", r"loan\s+(repayment|deduction|installment|instalment)", r"\binstall?ment\b"],
        "explanations": {
            "en": "EMI: A fixed payment made every month to repay a loan.",
            "hi": "EMI: Loan चुकाने के लिए हर महीने दी जाने वाली fixed किस्त।",
            "mr": "EMI: Loan फेडण्यासाठी दर महिन्याला भरायची fixed किस्त.",
        },
    },
    "debit": {
        "patterns": [r"\bdebit\b", r"\bwithdrawal\b", r"\bpaid\b", r"\bpayment\b", r"\bdr\b"],
        "explanations": {
            "en": "Debit: Money leaving your account.",
            "hi": "Debit: खाते से पैसा बाहर गया।",
            "mr": "Debit: खात्यातून पैसे गेले.",
        },
    },
    "credit": {
        "patterns": [r"\bcredit\b", r"\bdeposit\b", r"\breceived\b", r"\bsalary\b", r"\bcr\b"],
        "explanations": {
            "en": "Credit: Money entering your account.",
            "hi": "Credit: खाते में पैसा आया।",
            "mr": "Credit: खात्यात पैसे आले.",
        },
    },
    "interest": {
        "patterns": [r"\binterest\b", r"\bint\.?\b", r"\brate of interest\b", r"\broi\b"],
        "explanations": {
            "en": "Interest: Extra money paid on a loan or earned on savings.",
            "hi": "Interest: Loan पर दिया गया या savings पर मिला extra पैसा।",
            "mr": "Interest: Loan वर दिलेले किंवा savings वर मिळालेले extra पैसे.",
        },
    },
    "minimum_balance": {
        "patterns": [r"minimum\s+balance", r"\bmin\.?\s*bal", r"non[- ]maintenance"],
        "explanations": {
            "en": "Minimum balance: The lowest amount the bank expects you to keep in the account.",
            "hi": "Minimum balance: खाते में रखने के लिए bank द्वारा कही गई कम से कम राशि।",
            "mr": "Minimum balance: खात्यात ठेवायला सांगितलेली किमान रक्कम.",
        },
    },
    "closing_balance": {
        "patterns": [r"closing\s+balance", r"available\s+balance", r"balance\s+as\s+on"],
        "explanations": {
            "en": "Closing balance: The amount left after all listed transactions.",
            "hi": "Closing balance: सभी transactions के बाद खाते में बची राशि।",
            "mr": "Closing balance: सर्व transactions नंतर खात्यात उरलेली रक्कम.",
        },
    },
}


RISK_RULES: list[dict[str, Any]] = [
    {
        "name": "fees",
        "severity": "medium",
        "patterns": [r"\bcharge(s)?\b", r"\bfee(s)?\b", r"\bpenalt(y|ies)\b", r"\bfine\b", r"non[- ]maintenance"],
        "messages": {
            "en": "A fee, charge, fine, or penalty appears. Ask why it was applied and whether it can be avoided.",
            "hi": "Fee, charge, fine या penalty दिख रही है। Bank से पूछें कि यह क्यों लगी और क्या इससे बचा जा सकता है।",
            "mr": "Fee, charge, fine किंवा penalty दिसत आहे. ती का लागली आणि टाळता येते का ते bank ला विचारा.",
        },
    },
    {
        "name": "loan_or_emi",
        "severity": "medium",
        "patterns": [r"\bemi\b", r"loan\s+(deduction|repayment)", r"\binstall?ment\b", r"auto[- ]debit"],
        "messages": {
            "en": "A loan/EMI deduction appears. Check that the amount and date match what you agreed to.",
            "hi": "Loan/EMI deduction दिख रही है। Amount और date आपके agreement से match करते हैं या नहीं check करें।",
            "mr": "Loan/EMI deduction दिसत आहे. Amount आणि date agreement प्रमाणे आहेत का तपासा.",
        },
    },
    {
        "name": "minimum_balance",
        "severity": "low",
        "patterns": [r"minimum\s+balance", r"non[- ]maintenance", r"low\s+balance"],
        "messages": {
            "en": "A minimum balance rule may apply. Low balance can lead to extra fees.",
            "hi": "Minimum balance rule लागू हो सकता है। Balance कम होने पर extra fee लग सकती है।",
            "mr": "Minimum balance rule लागू असू शकतो. Balance कमी असेल तर extra fee लागू शकते.",
        },
    },
    {
        "name": "legal_consent",
        "severity": "high",
        "patterns": [r"\bwaive\b", r"\bforeclos", r"\bguarantor\b", r"\bcollateral\b", r"\barbitration\b", r"\birrevocable\b", r"\bconsent\b"],
        "messages": {
            "en": "This document may contain a legal/consent clause. Read it carefully and ask an authorized person before signing.",
            "hi": "इस document में legal/consent clause हो सकता है। Sign करने से पहले ध्यान से पढ़ें और authorized person से पूछें।",
            "mr": "या document मध्ये legal/consent clause असू शकतो. सही करण्यापूर्वी नीट वाचा आणि authorized person ला विचारा.",
        },
    },
]


SAMPLE_DOCUMENT = """
Bank Statement
Statement Period: 01/06/2026 to 25/06/2026
Opening Balance: Rs. 15,000
03/06/2026 Salary Credit Rs. 25,000 Balance Rs. 40,000
05/06/2026 Grocery Debit Rs. 2,200 Balance Rs. 37,800
09/06/2026 ATM Withdrawal Rs. 5,000 Balance Rs. 32,800
12/06/2026 EMI Loan Deduction Rs. 12,000 Balance Rs. 20,800
18/06/2026 Government Scheme Benefit Credit Rs. 2,000 Balance Rs. 22,800
25/06/2026 Medical Payment Debit Rs. 18,500 Balance Rs. 4,300
Closing Balance: Rs. 4,300
""".strip()


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    source_type: str
    warnings: list[str]


@dataclass(frozen=True)
class RiskFlag:
    severity: str
    message: str
    evidence: str


@dataclass(frozen=True)
class AnalysisResult:
    key_details: dict[str, str]
    term_explanations: list[str]
    risk_flags: list[RiskFlag]
    high_risk_clauses: list[str]
    summary: str
    next_steps: list[str]
    confidence_notes: list[str]


def t(language: str, key: str) -> str:
    """Return translated text, falling back to English."""
    return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def decode_text_bytes(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return file_bytes.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore").strip()


def extract_text_from_upload(uploaded_file: Any, language: str) -> ExtractionResult:
    """Extract text from TXT/CSV/PDF/image uploads with OCR fallback when available."""
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()
    warnings: list[str] = []

    if filename.endswith((".txt", ".csv")):
        text = decode_text_bytes(file_bytes)
        if filename.endswith(".csv"):
            text = csv_to_readable_text(text)
        return ExtractionResult(text=text, source_type="text", warnings=warnings)

    if filename.endswith(".pdf"):
        direct_text = extract_text_from_pdf(file_bytes)
        if len(normalize_text(direct_text)) >= 80:
            return ExtractionResult(text=direct_text, source_type="pdf_text", warnings=warnings)

        ocr_text, ocr_warning = ocr_pdf(file_bytes)
        if ocr_warning:
            warnings.append(ocr_warning or t(language, "ocr_missing"))

        combined_text = "\n".join(part for part in [direct_text, ocr_text] if normalize_text(part))
        if direct_text and not ocr_text:
            warnings.append(t(language, "analysis_warning"))
        return ExtractionResult(text=combined_text, source_type="pdf_ocr", warnings=warnings)

    if filename.endswith((".png", ".jpg", ".jpeg")):
        image_text, ocr_warning = ocr_image(file_bytes)
        if ocr_warning:
            warnings.append(ocr_warning or t(language, "ocr_missing"))
        return ExtractionResult(text=image_text, source_type="image_ocr", warnings=warnings)

    return ExtractionResult(text="", source_type="unknown", warnings=[t(language, "no_text")])


def csv_to_readable_text(raw_csv: str) -> str:
    try:
        reader = csv.DictReader(io.StringIO(raw_csv))
        if not reader.fieldnames:
            return raw_csv
        rows = []
        for row in reader:
            row_text = ", ".join(f"{key}: {value}" for key, value in row.items() if value)
            if row_text:
                rows.append(row_text)
        return "\n".join(rows) or raw_csv
    except csv.Error:
        return raw_csv


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts: list[str] = []

    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    except Exception:
        pass

    if normalize_text("\n".join(text_parts)):
        return "\n".join(text_parts)

    try:
        import fitz

        document = fitz.open(stream=file_bytes, filetype="pdf")
        for page in document:
            text_parts.append(page.get_text("text") or "")
    except Exception:
        pass

    return "\n".join(text_parts).strip()


def ocr_image(file_bytes: bytes) -> tuple[str, str | None]:
    try:
        from PIL import Image, ImageOps
        import pytesseract
    except Exception:
        return "", "OCR libraries are not installed. Add pytesseract and pillow, and ensure Tesseract is available."

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        return pytesseract.image_to_string(image).strip(), None
    except Exception as exc:
        return "", f"OCR could not read this image: {exc}"


def ocr_pdf(file_bytes: bytes, max_pages: int = 3) -> tuple[str, str | None]:
    try:
        import fitz
    except Exception:
        return "", "PDF OCR fallback needs PyMuPDF. Direct PDF text extraction may still work."

    text_parts: list[str] = []
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
        for page_index, page in enumerate(document):
            if page_index >= max_pages:
                break
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_bytes = pixmap.tobytes("png")
            page_text, warning = ocr_image(image_bytes)
            if warning:
                return "\n".join(text_parts), warning
            text_parts.append(page_text)
    except Exception as exc:
        return "\n".join(text_parts), f"Scanned PDF OCR failed: {exc}"

    warning = None
    if len(document) > max_pages:
        warning = f"OCR was limited to the first {max_pages} pages to keep the app fast."
    return "\n".join(text_parts).strip(), warning


def detect_money_amounts(text: str) -> list[str]:
    amount_pattern = r"(?:₹|Rs\.?|INR)\s?\d[\d,]*(?:\.\d{1,2})?|\b\d[\d,]*(?:\.\d{1,2})?\s?(?:rupees|rs)\b"
    matches = re.findall(amount_pattern, text, flags=re.IGNORECASE)
    return list(dict.fromkeys(match.strip() for match in matches))[:12]


def detect_dates(text: str) -> list[str]:
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}\b",
    ]
    dates: list[str] = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return list(dict.fromkeys(dates))[:12]


def detect_account_number(text: str) -> str | None:
    match = re.search(r"(?:account|a/c|acct)[^\d]{0,30}(\d{6,18})", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def find_labeled_amount(text: str, labels: list[str]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:{label_pattern})[^\d₹R]{{0,40}}((?:₹|Rs\.?|INR)?\s?\d[\d,]*(?:\.\d{{1,2}})?)",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def explain_financial_terms(text: str, language: str) -> list[str]:
    lowered = text.lower()
    explanations: list[str] = []
    for rule in TERM_RULES.values():
        if any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in rule["patterns"]):
            explanations.append(rule["explanations"].get(language, rule["explanations"]["en"]))
    return explanations


def snippet_for_pattern(text: str, pattern: str, radius: int = 70) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""
    start = max(match.start() - radius, 0)
    end = min(match.end() + radius, len(text))
    return normalize_text(text[start:end])


def flag_risky_clauses(text: str, language: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    for rule in RISK_RULES:
        for pattern in rule["patterns"]:
            evidence = snippet_for_pattern(text, pattern)
            if evidence:
                flags.append(
                    RiskFlag(
                        severity=rule["severity"],
                        message=rule["messages"].get(language, rule["messages"]["en"]),
                        evidence=evidence,
                    )
                )
                break

    percent_values = [float(value) for value in re.findall(r"\b(\d{1,2}(?:\.\d+)?)\s?%", text)]
    if any(value >= 15 for value in percent_values):
        messages = {
            "en": "A high interest/rate percentage appears. Understand the total cost before signing.",
            "hi": "High interest/rate percentage दिख रही है। Sign करने से पहले total cost समझें।",
            "mr": "High interest/rate percentage दिसत आहे. सही करण्यापूर्वी total cost समजून घ्या.",
        }
        flags.append(RiskFlag("high", messages.get(language, messages["en"]), f"Detected rates: {percent_values}"))

    return dedupe_risks(flags)


def dedupe_risks(flags: list[RiskFlag]) -> list[RiskFlag]:
    seen: set[str] = set()
    unique: list[RiskFlag] = []
    for flag in flags:
        if flag.message not in seen:
            unique.append(flag)
            seen.add(flag.message)
    return unique[:8]


def generate_user_summary(text: str, language: str) -> AnalysisResult:
    clean_text = normalize_text(text)
    dates = detect_dates(clean_text)
    amounts = detect_money_amounts(clean_text)
    account_number = detect_account_number(clean_text)
    opening_balance = find_labeled_amount(clean_text, ["opening balance", "opening bal"])
    closing_balance = find_labeled_amount(clean_text, ["closing balance", "available balance", "closing bal", "balance"])
    term_explanations = explain_financial_terms(clean_text, language)
    risk_flags = flag_risky_clauses(clean_text, language)

    key_details = {
        t(language, "possible_period"): " - ".join([dates[0], dates[-1]]) if len(dates) >= 2 else t(language, "not_found"),
        t(language, "opening_balance"): opening_balance or (amounts[0] if amounts else t(language, "not_found")),
        t(language, "closing_balance"): closing_balance or (amounts[-1] if amounts else t(language, "not_found")),
        t(language, "account_number"): account_number or t(language, "not_found"),
        t(language, "amounts"): ", ".join(amounts[:6]) if amounts else t(language, "not_found"),
        t(language, "dates"): ", ".join(dates[:6]) if dates else t(language, "not_found"),
    }

    summary = build_plain_summary(clean_text, language, bool(risk_flags))
    next_steps = build_next_steps(clean_text, risk_flags, language)
    confidence_notes = build_confidence_notes(clean_text, amounts, dates, language)
    high_risk_clauses = [flag.evidence for flag in risk_flags if flag.severity == "high" and flag.evidence]

    return AnalysisResult(
        key_details=key_details,
        term_explanations=term_explanations,
        risk_flags=risk_flags,
        high_risk_clauses=high_risk_clauses,
        summary=summary,
        next_steps=next_steps,
        confidence_notes=confidence_notes,
    )


def build_plain_summary(text: str, language: str, has_risks: bool) -> str:
    lowered = text.lower()
    parts = [t(language, "summary_intro"), t(language, "summary_use")]

    signals = {
        "salary": any(word in lowered for word in ["salary", "wage", "income"]),
        "scheme": any(word in lowered for word in ["scheme", "benefit", "subsidy", "government"]),
        "emi": any(word in lowered for word in ["emi", "loan", "installment", "instalment"]),
        "medical": any(word in lowered for word in ["medical", "hospital", "clinic"]),
        "insurance": any(word in lowered for word in ["insurance", "premium", "policy"]),
    }

    if language == "hi":
        if signals["salary"]:
            parts.append("Salary या income deposit दिख रही है।")
        if signals["scheme"]:
            parts.append("Government scheme या benefit से जुड़ी राशि दिख रही है।")
        if signals["emi"]:
            parts.append("Loan/EMI से जुड़ी कटौती या शर्त दिख रही है।")
        if signals["medical"]:
            parts.append("Medical payment दिख रहा है, जो balance कम कर सकता है।")
        if signals["insurance"]:
            parts.append("Insurance policy या premium से जुड़ी बात दिख रही है।")
    elif language == "mr":
        if signals["salary"]:
            parts.append("Salary किंवा income deposit दिसत आहे.")
        if signals["scheme"]:
            parts.append("Government scheme किंवा benefit शी संबंधित रक्कम दिसत आहे.")
        if signals["emi"]:
            parts.append("Loan/EMI शी संबंधित deduction किंवा term दिसत आहे.")
        if signals["medical"]:
            parts.append("Medical payment दिसत आहे, ज्यामुळे balance कमी होऊ शकतो.")
        if signals["insurance"]:
            parts.append("Insurance policy किंवा premium शी संबंधित गोष्ट दिसत आहे.")
    else:
        if signals["salary"]:
            parts.append("Salary or income appears to have been deposited.")
        if signals["scheme"]:
            parts.append("A government scheme or benefit amount appears.")
        if signals["emi"]:
            parts.append("A loan/EMI deduction or term appears.")
        if signals["medical"]:
            parts.append("A medical payment appears and may reduce the balance.")
        if signals["insurance"]:
            parts.append("Insurance policy or premium information appears.")

    if has_risks:
        parts.append(
            {
                "en": "Some items need careful checking before making a decision.",
                "hi": "कुछ बातों को फैसला लेने से पहले ध्यान से check करना चाहिए।",
                "mr": "काही गोष्टी निर्णय घेण्यापूर्वी नीट check कराव्यात.",
            }.get(language, "Some items need careful checking before making a decision.")
        )

    return " ".join(parts)


def build_next_steps(text: str, risks: list[RiskFlag], language: str) -> list[str]:
    if language == "hi":
        steps = [
            "Dates, amounts और balance को original document से मिलाएं।",
            "जिस transaction या clause को आप नहीं पहचानतीं, उसके बारे में bank से पूछें।",
            "Important decision लेने से पहले authorized advisor या official office से verify करें।",
        ]
        if risks:
            steps.insert(1, "Flag की गई charges, EMI, legal clauses या penalties को सबसे पहले check करें।")
    elif language == "mr":
        steps = [
            "Dates, amounts आणि balance original document शी match करा.",
            "जो transaction किंवा clause ओळखीचा नाही, त्याबद्दल bank ला विचारा.",
            "Important decision घेण्यापूर्वी authorized advisor किंवा official office कडून verify करा.",
        ]
        if risks:
            steps.insert(1, "Flag केलेल्या charges, EMI, legal clauses किंवा penalties आधी check करा.")
    else:
        steps = [
            "Match dates, amounts, and balances against the original document.",
            "Ask your bank about any transaction or clause you do not recognize.",
            "Verify important decisions with an authorized advisor or official office.",
        ]
        if risks:
            steps.insert(1, "Check the flagged charges, EMI items, legal clauses, or penalties first.")

    if "emi" in text.lower() or "loan" in text.lower():
        steps.append(
            {
                "en": "If possible, keep at least one EMI amount available before the next due date.",
                "hi": "अगर possible हो, next due date से पहले कम से कम एक EMI जितना balance रखें।",
                "mr": "शक्य असल्यास, next due date आधी किमान एका EMI इतका balance ठेवा.",
            }.get(language, "")
        )
    return steps


def build_confidence_notes(text: str, amounts: list[str], dates: list[str], language: str) -> list[str]:
    if len(text) < 80:
        return [t(language, "low_confidence")]
    if amounts or dates:
        return [t(language, "good_confidence")]
    return [t(language, "medium_confidence")]


def build_report(text: str, analysis: AnalysisResult, language: str) -> str:
    lines = [
        f"# {t(language, 'title')} Summary Report",
        "",
        "## " + t(language, "simple_explanation"),
        analysis.summary,
        "",
        "## " + t(language, "key_details"),
    ]
    lines.extend(f"- {key}: {value}" for key, value in analysis.key_details.items())
    lines.append("")
    lines.append("## " + t(language, "risk_flags"))
    if analysis.risk_flags:
        lines.extend(f"- [{flag.severity.upper()}] {flag.message} Evidence: {flag.evidence}" for flag in analysis.risk_flags)
    else:
        lines.append("- " + t(language, "no_risks"))
    lines.append("")
    lines.append("## " + t(language, "next_steps"))
    lines.extend(f"- {step}" for step in analysis.next_steps)
    lines.append("")
    lines.append("## " + t(language, "confidence"))
    lines.extend(f"- {note}" for note in analysis.confidence_notes)
    lines.append("")
    lines.append("## " + t(language, "disclaimer"))
    lines.append(t(language, "disclaimer"))
    lines.append("")
    lines.append("## " + t(language, "extracted_text"))
    lines.append(text)
    return "\n".join(lines)


def render_key_details(analysis: AnalysisResult) -> None:
    cols = st.columns(2)
    for index, (label, value) in enumerate(analysis.key_details.items()):
        with cols[index % 2]:
            st.metric(label=label, value=value)


def render_risks(analysis: AnalysisResult, language: str) -> None:
    if not analysis.risk_flags:
        st.success(t(language, "no_risks"))
        return

    for flag in analysis.risk_flags:
        message = f"**{flag.severity.title()} risk:** {flag.message}"
        if flag.severity == "high":
            st.error(message)
        elif flag.severity == "medium":
            st.warning(message)
        else:
            st.info(message)
        if flag.evidence:
            st.caption(f"Evidence: {flag.evidence}")


def render_app() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="💬", layout="wide")

    language_name_to_code = {TRANSLATIONS[code]["language_name"]: code for code in SUPPORTED_LANGUAGES}

    with st.sidebar:
        selected_language_name = st.selectbox(
            "Language / भाषा",
            options=list(language_name_to_code.keys()),
            index=0,
        )
        language = language_name_to_code[selected_language_name]
        st.warning(t(language, "disclaimer"), icon="⚠️")

    st.title(t(language, "title"))
    st.subheader(t(language, "subtitle"))
    st.write(t(language, "description"))

    uploaded_file = st.file_uploader(
        t(language, "uploader_label"),
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"],
        help=t(language, "upload_help"),
    )

    col_sample, col_analyze = st.columns([1, 1])
    with col_sample:
        use_sample = st.button(t(language, "sample_button"), type="secondary")
    with col_analyze:
        analyze_clicked = st.button(t(language, "analyze_button"), type="primary", disabled=uploaded_file is None)

    text_to_analyze = ""
    extraction_warnings: list[str] = []

    if use_sample:
        text_to_analyze = SAMPLE_DOCUMENT
        st.success(t(language, "sample_loaded"))
    elif uploaded_file is not None and analyze_clicked:
        with st.spinner("Reading document..."):
            extraction = extract_text_from_upload(uploaded_file, language)
        text_to_analyze = extraction.text
        extraction_warnings = extraction.warnings

    if not text_to_analyze:
        if uploaded_file is not None:
            st.info(t(language, "ready_to_analyze"))
        else:
            st.info(t(language, "no_document"))
        return

    for warning in extraction_warnings:
        st.warning(warning)

    if len(normalize_text(text_to_analyze)) < 20:
        st.error(t(language, "no_text"))
        return

    with st.spinner("Analyzing financial details..."):
        analysis = generate_user_summary(text_to_analyze, language)

    if extraction_warnings:
        st.warning(t(language, "analysis_warning"))
    else:
        st.success(t(language, "analysis_ready"))

    tab_summary, tab_text = st.tabs([t(language, "simple_explanation"), t(language, "extracted_text")])

    with tab_summary:
        st.markdown("### " + t(language, "key_details"))
        render_key_details(analysis)

        st.markdown("### " + t(language, "simple_explanation"))
        st.write(analysis.summary)

        if analysis.term_explanations:
            st.markdown("### " + t(language, "terms_heading"))
            for explanation in analysis.term_explanations:
                st.info(explanation)

        st.markdown("### " + t(language, "risk_flags"))
        render_risks(analysis, language)

        if analysis.high_risk_clauses:
            st.markdown("### " + t(language, "high_risk"))
            for clause in analysis.high_risk_clauses:
                st.warning(clause)

        st.markdown("### " + t(language, "next_steps"))
        for step in analysis.next_steps:
            st.write(f"- {step}")

        st.markdown("### " + t(language, "confidence"))
        for note in analysis.confidence_notes:
            st.caption(note)

    with tab_text:
        st.text_area(t(language, "extracted_text"), value=text_to_analyze, height=360)

    report = build_report(text_to_analyze, analysis, language)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            t(language, "download_text"),
            data=text_to_analyze,
            file_name="dhandidi_extracted_text.txt",
            mime="text/plain",
        )
    with col2:
        st.download_button(
            t(language, "download_summary"),
            data=report,
            file_name="dhandidi_summary_report.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    render_app()
