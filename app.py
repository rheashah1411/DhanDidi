"""DhanDidi — accessible, dataset-assisted financial document simplifier."""

from __future__ import annotations

import html

import streamlit as st

from analysis import AnalysisResult, analyze_document
from dataset_kb import DatasetKnowledgeBase, load_knowledge_base
from document_reader import clean_text, extract_text
from styles import CSS
from translations import DOC_TYPES, LANGUAGES, TEXT

st.set_page_config(page_title="DhanDidi | धनदीदी", page_icon="🌿", layout="centered", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_knowledge_base() -> DatasetKnowledgeBase:
    """One process-wide load: uploads never trigger another dataset download.

    Streamlit's resource cache keeps the OCR reference index in memory across
    reruns and users; dataset_kb.py additionally caches it on disk across starts.
    """
    return load_knowledge_base()


def safe(value: object) -> str:
    return html.escape(str(value))


def card(title: str, body: str, extra_class: str = "") -> None:
    st.markdown(f'<section class="section-card {extra_class}"><h2>{safe(title)}</h2><p>{safe(body)}</p></section>', unsafe_allow_html=True)


def list_card(title: str, items: list[str], empty: str, extra_class: str = "") -> None:
    content = items or [empty]
    rows = "".join(f"<li>{safe(item)}</li>" for item in content)
    st.markdown(f'<section class="section-card {extra_class}"><h2>{safe(title)}</h2><ul>{rows}</ul></section>', unsafe_allow_html=True)


def make_report(result: AnalysisResult, language: str) -> str:
    t = TEXT[language]
    lines = [t["report_title"], "=" * len(t["report_title"]), "", t["document_type"], f'{DOC_TYPES[language][result.doc_type]} — {t["confidence"]}: {t[result.confidence]}', "", t["what_is"], result.purpose, "", t["meaning"], result.meaning, "", t["important"]]
    lines.extend(f"• {label}: {value}" for label, value in result.details)
    if not result.details:
        lines.append(f"• {t['no_details']}")
    for heading, values, fallback in ((t["careful"], result.risks, t["no_risks"]), (t["recommendations"], result.recommendations, ""), (t["questions"], result.questions, "")):
        lines.extend(["", heading]); lines.extend(f"• {item}" for item in (values or [fallback]))
    lines.extend(["", t["confidence_note"], "", t["disclaimer"]])
    return "\n".join(lines)


def render_result(result: AnalysisResult, language: str, extracted: str) -> None:
    t = TEXT[language]
    st.markdown(
        f'<section class="doc-card"><div class="doc-label">{safe(t["document_type"])}</div>'
        f'<div class="doc-type">{safe(DOC_TYPES[language][result.doc_type])}</div>'
        f'<span class="confidence">{safe(t["confidence"])}: {safe(t[result.confidence])}</span></section>',
        unsafe_allow_html=True,
    )
    card(t["what_is"], result.purpose)
    card(t["meaning"], result.meaning)
    if result.details:
        values = "".join(f'<div class="detail"><div class="detail-label">{safe(label)}</div><div class="detail-value">{safe(value)}</div></div>' for label, value in result.details)
        st.markdown(f'<section class="section-card"><h2>{safe(t["important"])}</h2><div class="detail-grid">{values}</div></section>', unsafe_allow_html=True)
    else:
        card(t["important"], t["no_details"])
    list_card(t["careful"], result.risks, t["no_risks"], "risk")
    list_card(t["recommendations"], result.recommendations, "")
    list_card(t["questions"], result.questions, "")
    if result.matches:
        card(t["similar"], t["similar_note"].format(count=len(result.matches)))
    st.info(t["confidence_note"], icon="ℹ️")
    with st.expander(t["extracted_text"]):
        st.text(extracted[:12000])
    st.download_button(t["download"], make_report(result, language), file_name="DhanDidi_explanation.txt", mime="text/plain")


# Loading happens once at application startup, before any upload is analysed.
knowledge_base = get_knowledge_base()

# Put the large language control first so changing language is the most obvious
# action on both phones and desktops. Native names avoid mixed-script options.
previous_name = st.session_state.get("language_picker", "English")
previous_language = LANGUAGES.get(previous_name, "en")
st.markdown(f'<div class="language-panel-title">{safe(TEXT[previous_language]["language"])}</div>', unsafe_allow_html=True)
language_name = st.selectbox(TEXT[previous_language]["language"], list(LANGUAGES), key="language_picker", label_visibility="visible")
language = LANGUAGES[language_name]
t = TEXT[language]

brand = "DhanDidi" if language == "en" else "धनदीदी"
st.markdown(
    f'<header class="hero"><div class="brand"><span class="brand-mark">🌿</span><span>{safe(brand)}</span></div>'
    f'<h1>{safe(t["hero_heading"])}</h1><p>{safe(t["hero_body"])}</p></header>',
    unsafe_allow_html=True,
)

st.markdown(f'<h2 style="color:#12304A;font-size:1.75rem;margin-top:1.6rem">{safe(t["tagline"])}</h2><p style="font-size:1.1rem;color:#52697C">{safe(t["subtitle"])}</p>', unsafe_allow_html=True)
st.markdown(f'<div class="privacy">{safe(t["privacy"])}</div>', unsafe_allow_html=True)
status = t["dataset_ready"] if knowledge_base.status == "ready" else t["dataset_fallback"]
st.markdown(f'<div class="status">● {safe(status)}</div>', unsafe_allow_html=True)

st.markdown(f'<section class="section-card"><h2>{safe(t["upload_title"])}</h2><p>{safe(t["upload_help"])}</p>', unsafe_allow_html=True)
uploaded = st.file_uploader(t["upload_label"], type=["pdf", "png", "jpg", "jpeg", "txt", "csv"], label_visibility="collapsed")
st.markdown("</section>", unsafe_allow_html=True)

if uploaded is not None:
    if st.button(t["analyze"], type="primary", use_container_width=True):
        try:
            with st.spinner(t["processing"]):
                extracted_text = clean_text(extract_text(uploaded.name, uploaded.getvalue()))
                if len(extracted_text) < 25:
                    st.warning(t["ocr_error"], icon="📷")
                else:
                    result = analyze_document(extracted_text, language, knowledge_base)
                    st.session_state["analysis"] = (result, language, extracted_text, uploaded.name)
        except Exception:
            st.error(t["file_error"], icon="⚠️")

saved = st.session_state.get("analysis")
if saved and (uploaded is None or saved[3] == uploaded.name):
    result, saved_language, extracted_text, _ = saved
    if saved_language != language:
        result = analyze_document(extracted_text, language, knowledge_base)
        st.session_state["analysis"] = (result, language, extracted_text, saved[3])
    render_result(result, language, extracted_text)

st.markdown(
    f'<section class="section-card"><h2>{safe(t["how_title"])}</h2><div class="steps">'
    f'<div class="step">{safe(t["step1"])}</div><div class="step">{safe(t["step2"])}</div><div class="step">{safe(t["step3"])}</div></div></section>',
    unsafe_allow_html=True,
)
st.markdown(f'<div class="footer-note">{safe(t["disclaimer"])}<br>{safe(t["footer"])}</div>', unsafe_allow_html=True)
