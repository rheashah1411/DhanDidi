"""DhanDidi: self-contained two-file Streamlit deployment."""
from __future__ import annotations

import html
import io
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract

st.set_page_config(page_title="DhanDidi | धनदीदी", page_icon="🌿", layout="centered")

CSS = """
<style>
:root{--navy:#12304a;--teal:#087f7b;--aqua:#20b8b2;--ink:#17324d}
.stApp{background:linear-gradient(145deg,#f9fcfd,#edfaf9 55%,#f5faff)}
.block-container{max-width:960px;padding:1.5rem 1.2rem 5rem}
html,body,[class*=css]{font-family:Arial,"Noto Sans Devanagari",sans-serif;color:var(--ink)}
.hero{background:linear-gradient(135deg,var(--navy),#125b70 60%,var(--teal));color:white;border-radius:28px;padding:2rem 2.2rem;box-shadow:0 18px 45px #12304a24;margin:1rem 0 1.5rem}
.hero h1{color:white;font-size:clamp(2rem,6vw,3.3rem);line-height:1.1;margin:.8rem 0}.hero p{color:#e5fbfa;font-size:1.1rem;line-height:1.6}.brand{font-size:1.2rem;font-weight:800}
.section{background:white;border:1px solid #d7ecee;border-radius:21px;padding:1.35rem 1.5rem;box-shadow:0 8px 26px #12304a10;margin:.9rem 0}.section h2{color:var(--navy);font-size:1.4rem;margin:0 0 .65rem}.section p,.section li{font-size:1.05rem;line-height:1.65}
.doc{background:linear-gradient(135deg,#e6faf7,#edf6ff);border:2px solid #68cfcb;border-radius:24px;padding:1.5rem 1.7rem;margin:1.5rem 0}.doc-label{font-weight:700;color:#326078}.doc-type{font-size:2rem;font-weight:800;color:var(--navy);margin:.25rem 0}.pill{display:inline-block;background:white;border:1px solid #83d8d4;border-radius:999px;padding:.3rem .75rem;color:#086b68;font-weight:700}
.privacy{background:#e6f7f3;color:#174f51;border-radius:14px;padding:.8rem 1rem;margin:1rem 0}.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.7rem}.detail{background:#f3fafc;border-left:4px solid var(--aqua);border-radius:12px;padding:.8rem}.detail small{display:block;color:#52697c;font-weight:700}.detail strong{color:var(--navy);overflow-wrap:anywhere}
[data-baseweb=select]>div{min-height:55px;border:2px solid #78c9c7!important;border-radius:14px!important;font-size:1.1rem}[data-testid=stFileUploader]{background:white;border:2px dashed #62bfbc;border-radius:18px;padding:.6rem}.stButton>button,.stDownloadButton>button{min-height:56px;border-radius:15px!important;font-size:1.08rem!important;font-weight:800!important;width:100%}.stButton>button[kind=primary]{background:linear-gradient(135deg,var(--teal),#0b9993)!important;color:white!important;border:0!important}.status{font-size:.9rem;color:#467080}.footer{text-align:center;color:#5b7181;margin-top:2rem;line-height:1.5}
@media(max-width:640px){.block-container{padding:1rem .7rem 4rem}.hero{padding:1.5rem 1.2rem;border-radius:21px}.section{padding:1.1rem}.doc{padding:1.2rem}}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

LANGUAGES = {"English": "en", "हिन्दी": "hi", "मराठी": "mr"}
T = {
"en":{"language":"🌐 Choose your language","hero":"Money documents, made human.","hero_body":"Simple guidance for confident financial decisions — in the language you choose.","tag":"Understand your financial documents with confidence","sub":"Upload a document and get a clear, private, easy-to-follow explanation.","privacy":"🔒 Your document is processed for this analysis and is not intentionally stored.","upload":"Upload your financial document","formats":"PDF, image, text, or CSV • Maximum 20 MB","choose":"Choose a file","analyze":"✨ Explain my document","working":"Reading your document and comparing reference examples…","unreadable":"I could not read enough text. Try a clearer image or a text-based PDF.","error":"This file could not be read. Please try another copy.","dtype":"📄 Document Type","confidence":"Confidence","high":"High","medium":"Medium","low":"Low","what":"📖 What This Document Is","means":"💡 What It Means for You","important":"📌 Important Information","careful":"⚠️ Things to Be Careful About","advice":"🤖 DhanDidi Recommendations","questions":"❓ Questions to Ask","none":"No reliable key values were found. Check the original document carefully.","norisk":"No common warning phrases were found, but this is not a legal or financial guarantee.","reference":"Reference check","refnote":"Compared with {count} examples from the Indian financial-document dataset.","note":"This combines reference similarity with document rules. Confirm names, amounts, and dates against the original.","download":"⬇️ Download explanation","raw":"View text read from the document","ready":"Reference knowledge base ready","fallback":"Reference dataset unavailable; safe offline rules are active","disclaimer":"DhanDidi explains documents for education. It does not provide legal, investment, or financial advice."},
"hi":{"language":"🌐 अपनी भाषा चुनें","hero":"पैसों के दस्तावेज़, सरल शब्दों में।","hero_body":"आत्मविश्वास से वित्तीय निर्णय लेने के लिए आपकी चुनी हुई भाषा में सरल मार्गदर्शन।","tag":"अपने वित्तीय दस्तावेज़ आत्मविश्वास से समझें","sub":"दस्तावेज़ अपलोड करें और सरल, निजी तथा समझने योग्य जानकारी पाएँ।","privacy":"🔒 आपके दस्तावेज़ का उपयोग केवल इस विश्लेषण के लिए होता है; इसे जानबूझकर संग्रहीत नहीं किया जाता।","upload":"अपना वित्तीय दस्तावेज़ अपलोड करें","formats":"पीडीएफ़, चित्र, पाठ या सीएसवी • अधिकतम २० एमबी","choose":"फ़ाइल चुनें","analyze":"✨ मेरा दस्तावेज़ समझाएँ","working":"दस्तावेज़ पढ़कर संदर्भ उदाहरणों से मिलान किया जा रहा है…","unreadable":"पर्याप्त पाठ पढ़ा नहीं जा सका। अधिक साफ़ चित्र या पाठ-आधारित पीडीएफ़ अपलोड करें।","error":"यह फ़ाइल पढ़ी नहीं जा सकी। कृपया दूसरी प्रति आज़माएँ।","dtype":"📄 दस्तावेज़ का प्रकार","confidence":"विश्वसनीयता","high":"उच्च","medium":"मध्यम","low":"कम","what":"📖 यह दस्तावेज़ क्या है","means":"💡 आपके लिए इसका अर्थ","important":"📌 महत्वपूर्ण जानकारी","careful":"⚠️ किन बातों से सावधान रहें","advice":"🤖 धनदीदी की सलाह","questions":"❓ पूछने योग्य प्रश्न","none":"कोई भरोसेमंद मुख्य मूल्य नहीं मिला। मूल दस्तावेज़ ध्यान से जाँचें।","norisk":"कोई सामान्य चेतावनी वाला वाक्यांश नहीं मिला, पर यह कानूनी या वित्तीय गारंटी नहीं है।","reference":"संदर्भ जाँच","refnote":"भारतीय वित्तीय दस्तावेज़ आँकड़ा-संग्रह के {count} उदाहरणों से मिलान किया गया।","note":"यह परिणाम संदर्भ समानता और दस्तावेज़ नियमों को मिलाकर बना है। नाम, राशि और तारीख मूल दस्तावेज़ से मिलाएँ।","download":"⬇️ विवरण डाउनलोड करें","raw":"दस्तावेज़ से पढ़ा गया पाठ देखें","ready":"संदर्भ ज्ञान-संग्रह तैयार है","fallback":"संदर्भ आँकड़ा-संग्रह उपलब्ध नहीं है; सुरक्षित ऑफ़लाइन नियम सक्रिय हैं","disclaimer":"धनदीदी केवल जानकारी और समझ के लिए दस्तावेज़ समझाती है। यह कानूनी, निवेश या वित्तीय सलाह नहीं देती।"},
"mr":{"language":"🌐 तुमची भाषा निवडा","hero":"पैशांचे दस्तऐवज, सोप्या शब्दांत.","hero_body":"आत्मविश्वासाने आर्थिक निर्णय घेण्यासाठी तुम्ही निवडलेल्या भाषेत सोपे मार्गदर्शन.","tag":"तुमचे आर्थिक दस्तऐवज आत्मविश्वासाने समजून घ्या","sub":"दस्तऐवज अपलोड करा आणि सोपे, खासगी व समजण्यास सुलभ स्पष्टीकरण मिळवा.","privacy":"🔒 तुमचा दस्तऐवज केवळ या विश्लेषणासाठी वापरला जातो; तो जाणीवपूर्वक साठवला जात नाही.","upload":"तुमचा आर्थिक दस्तऐवज अपलोड करा","formats":"पीडीएफ, चित्र, मजकूर किंवा सीएसव्ही • कमाल २० एमबी","choose":"फाइल निवडा","analyze":"✨ माझा दस्तऐवज समजावून सांगा","working":"दस्तऐवज वाचून संदर्भ उदाहरणांशी तुलना केली जात आहे…","unreadable":"पुरेसा मजकूर वाचता आला नाही. अधिक स्पष्ट चित्र किंवा मजकूर असलेला पीडीएफ वापरा.","error":"ही फाइल वाचता आली नाही. कृपया दुसरी प्रत वापरून पाहा.","dtype":"📄 दस्तऐवजाचा प्रकार","confidence":"विश्वसनीयता","high":"उच्च","medium":"मध्यम","low":"कमी","what":"📖 हा दस्तऐवज काय आहे","means":"💡 तुमच्यासाठी याचा अर्थ","important":"📌 महत्त्वाची माहिती","careful":"⚠️ कोणत्या गोष्टींबाबत सावध राहावे","advice":"🤖 धनदीदीच्या सूचना","questions":"❓ विचारायचे प्रश्न","none":"खात्रीशीर महत्त्वाची मूल्ये सापडली नाहीत. मूळ दस्तऐवज काळजीपूर्वक तपासा.","norisk":"नेहमीचे इशारादर्शक शब्द सापडले नाहीत; तरीही ही कायदेशीर किंवा आर्थिक हमी नाही.","reference":"संदर्भ तपासणी","refnote":"भारतीय आर्थिक दस्तऐवज माहिती-संचातील {count} उदाहरणांशी तुलना केली.","note":"हा निकाल संदर्भ साम्य आणि दस्तऐवज नियम एकत्र करून तयार केला आहे. नावे, रक्कम आणि तारखा मूळ दस्तऐवजाशी जुळवा.","download":"⬇️ स्पष्टीकरण उतरवून घ्या","raw":"दस्तऐवजातून वाचलेला मजकूर पाहा","ready":"संदर्भ ज्ञानसंच तयार आहे","fallback":"संदर्भ माहिती-संच उपलब्ध नाही; सुरक्षित ऑफलाइन नियम सुरू आहेत","disclaimer":"धनदीदी केवळ माहिती व समज वाढवण्यासाठी दस्तऐवज समजावते. ती कायदेशीर, गुंतवणूक किंवा आर्थिक सल्ला देत नाही."}}

DOC = {
"en":{"bank_statement":"Bank Statement","cheque":"Cheque","tax_document":"Income-tax Document","salary_slip":"Salary Slip","utility_bill":"Utility Bill","loan_agreement":"Loan Agreement","insurance_policy":"Insurance Policy","scheme_form":"Government Scheme Form","credit_card_statement":"Credit Card Statement","investment_document":"Investment Document","pension_document":"Pension Document","fixed_deposit":"Fixed Deposit Document","unknown":"Financial Document"},
"hi":{"bank_statement":"बैंक खाता विवरण","cheque":"बैंक चेक","tax_document":"आयकर दस्तावेज़","salary_slip":"वेतन पर्ची","utility_bill":"उपयोगिता बिल","loan_agreement":"ऋण समझौता","insurance_policy":"बीमा पॉलिसी","scheme_form":"सरकारी योजना प्रपत्र","credit_card_statement":"क्रेडिट कार्ड विवरण","investment_document":"निवेश दस्तावेज़","pension_document":"पेंशन दस्तावेज़","fixed_deposit":"सावधि जमा दस्तावेज़","unknown":"वित्तीय दस्तावेज़"},
"mr":{"bank_statement":"बँक खातेविवरण","cheque":"बँक धनादेश","tax_document":"प्राप्तिकर दस्तऐवज","salary_slip":"वेतन पावती","utility_bill":"उपयुक्तता सेवा देयक","loan_agreement":"कर्ज करार","insurance_policy":"विमा पॉलिसी","scheme_form":"शासकीय योजना अर्ज","credit_card_statement":"पतपत्र खातेविवरण","investment_document":"गुंतवणूक दस्तऐवज","pension_document":"निवृत्तिवेतन दस्तऐवज","fixed_deposit":"मुदत ठेव दस्तऐवज","unknown":"आर्थिक दस्तऐवज"}}

ANCHORS = {
"bank_statement":"account statement opening balance closing balance debit credit transaction narration IFSC",
"cheque":"pay bearer rupees only account payee cheque signature MICR IFSC",
"tax_document":"form 16 income tax TDS employer employee PAN assessment year gross salary deduction",
"salary_slip":"salary slip payslip employee basic pay allowance deduction provident fund net pay gross pay",
"utility_bill":"bill consumer number meter reading units due date amount payable electricity water gas"}
FOLDERS = {"Bank Statement":"bank_statement","Check":"cheque","ITR_Form 16":"tax_document","Salary Slip":"salary_slip","Utility":"utility_bill"}
KEYWORDS = {
"bank_statement":{"bank statement":9,"account statement":8,"closing balance":5,"transaction":2},"cheque":{"cheque":9,"bearer":4,"payee":4,"micr":3},"tax_document":{"form 16":10,"income tax":6,"tds":5,"assessment year":4},"salary_slip":{"salary slip":10,"payslip":9,"gross pay":5,"net pay":5},"utility_bill":{"electricity bill":9,"water bill":9,"consumer number":5,"meter reading":5},"loan_agreement":{"loan agreement":10,"borrower":5,"lender":5,"emi":4,"collateral":4},"insurance_policy":{"insurance policy":10,"policy number":5,"sum assured":5,"premium":4},"scheme_form":{"government scheme":8,"beneficiary":5,"eligibility":4,"yojana":5},"credit_card_statement":{"credit card":9,"minimum amount due":6,"credit limit":5},"investment_document":{"mutual fund":7,"investment":4,"folio":6,"nav":5},"pension_document":{"pension":8,"ppo":6,"annuity":5},"fixed_deposit":{"fixed deposit":9,"term deposit":8,"maturity amount":5}}

def tokens(text): return re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", text.lower())

def ocr(image):
    image = ImageOps.exif_transpose(image).convert("L"); image.thumbnail((2000,2000))
    image = ImageEnhance.Contrast(image).enhance(1.7).filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(image, config="--psm 6", timeout=12)

@st.cache_resource(show_spinner=False)
def load_kb():
    """Download and OCR the Kaggle dataset once per deployment process."""
    cache = Path(os.getenv("DHANDIDI_CACHE_DIR", ".cache")); cache.mkdir(exist_ok=True)
    index = cache / "dataset_index.json"
    if index.exists():
        payload=json.loads(index.read_text("utf-8"))
        if isinstance(payload,dict):
            payload=[{"type":x.get("type",x.get("doc_type","unknown")),"text":x["text"],"source":x["source"]} for x in payload.get("examples",[])]
        if payload:return payload,"ready"
    try:
        import kagglehub
        root = Path(kagglehub.dataset_download("mehaksingal/personal-financial-dataset-for-india"))
        examples=[]
        for folder, kind in FOLDERS.items():
            directory=next((p for p in root.rglob(folder) if p.is_dir()),None)
            paths=sorted(directory.glob("*.jpg")) if directory else []
            for path in paths[:2]:
                try: text=ocr(Image.open(path))
                except Exception: text=""
                examples.append({"type":kind,"text":ANCHORS[kind]+" "+text,"source":f"{folder}/{path.name}"})
        if not examples: raise RuntimeError("empty dataset")
        index.write_text(json.dumps(examples,ensure_ascii=False),"utf-8")
        return examples,"ready"
    except Exception:
        return [{"type":k,"text":v,"source":"offline reference"} for k,v in ANCHORS.items()],"fallback"

def retrieve(text, kb, limit=4):
    query=set(tokens(text)); scored=[]
    for item in kb:
        ref=set(tokens(item["text"])); union=query|ref
        score=len(query&ref)/max(math.sqrt(len(query)*len(ref)),1)
        scored.append((score,item))
    return sorted(scored,key=lambda x:x[0],reverse=True)[:limit]

def classify(text,kb):
    lower=text.lower(); scores={k:sum(w for phrase,w in v.items() if phrase in lower) for k,v in KEYWORDS.items()}
    for score,item in retrieve(text,kb,8): scores[item["type"]]=scores.get(item["type"],0)+score*6
    ordered=sorted(scores.items(),key=lambda x:x[1],reverse=True); kind,best=ordered[0]; second=ordered[1][1]
    if best<2.2:return "unknown","low"
    return kind,("high" if best>=8 and best-second>=3 else "medium" if best>=4 else "low")

FIELD_PATTERNS = {
"account":[r"(?:account|a/c)\s*(?:no\.?|number)?\s*[:#-]?\s*([xX*\d -]{6,24})"],"interest":[r"(?:interest|rate of interest)\s*(?:rate)?\s*[:@-]?\s*(\d{1,2}(?:\.\d+)?)\s*%"],"emi":[r"(?:emi|monthly instalment|monthly installment)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"premium":[r"premium\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"cover":[r"(?:sum assured|coverage amount)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"net":[r"(?:net pay|net salary|take home)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"due":[r"(?:total amount due|amount payable|amount due)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"balance":[r"(?:closing|available) balance\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],"due_date":[r"(?:payment )?due date\s*[:#-]?\s*([0-3]?\d[./-][01]?\d[./-](?:\d{2}|\d{4}))"]}
LABELS={"en":{"account":"Account number (protected)","interest":"Interest rate","emi":"Monthly instalment","premium":"Premium","cover":"Insurance cover","net":"Net pay","due":"Amount due","balance":"Closing balance","due_date":"Due date"},"hi":{"account":"खाता संख्या (सुरक्षित)","interest":"ब्याज दर","emi":"मासिक किस्त","premium":"बीमा किस्त","cover":"बीमा सुरक्षा राशि","net":"प्राप्त वेतन","due":"देय राशि","balance":"अंतिम शेष","due_date":"भुगतान की अंतिम तारीख"},"mr":{"account":"खाते क्रमांक (सुरक्षित)","interest":"व्याजदर","emi":"मासिक हप्ता","premium":"विम्याचा हप्ता","cover":"विमा संरक्षण रक्कम","net":"हाती मिळणारे वेतन","due":"देय रक्कम","balance":"अखेरची शिल्लक","due_date":"भरण्याची अंतिम तारीख"}}

RISK_RULES=[(r"(?:late|delay).{0,35}(?:fee|charge|penalt)","late"),(r"auto(?:matic)?\s*(?:debit|deduction)|nach mandate","auto"),(r"guarantor|jointly and severally","guarantor"),(r"collateral|mortgage|security interest","collateral"),(r"foreclosure|prepayment charge","early"),(r"exclusion|not covered|waiting period","exclude"),(r"minimum amount due","minimum"),(r"consent to share|share your (?:data|information)|third part","data")]
RISK={"en":{"late":"Late payment may cause a fee or penalty.","auto":"Money may be deducted automatically; check the amount and date.","guarantor":"A guarantor may become responsible if the borrower does not pay.","collateral":"A pledged asset may be at risk if payments are missed.","early":"Early repayment may have a charge.","exclude":"Some situations may not be covered by this insurance.","minimum":"Paying only the minimum can leave debt and add interest.","data":"Personal information may be shared with another organisation."},"hi":{"late":"देरी से भुगतान करने पर शुल्क या जुर्माना लग सकता है।","auto":"राशि अपने-आप कट सकती है; राशि और तारीख जाँचें।","guarantor":"ऋण लेने वाला भुगतान न करे तो जमानतदार को भुगतान करना पड़ सकता है।","collateral":"किस्त न चुकाने पर गिरवी संपत्ति खतरे में पड़ सकती है।","early":"समयपूर्व भुगतान पर शुल्क लग सकता है।","exclude":"कुछ स्थितियाँ इस बीमा में शामिल नहीं हो सकतीं।","minimum":"केवल न्यूनतम राशि चुकाने से कर्ज और ब्याज बढ़ सकता है।","data":"निजी जानकारी दूसरी संस्था से साझा की जा सकती है।"},"mr":{"late":"उशिरा पैसे भरल्यास शुल्क किंवा दंड लागू शकतो.","auto":"रक्कम आपोआप वजा होऊ शकते; रक्कम आणि तारीख तपासा.","guarantor":"कर्जदाराने पैसे न भरल्यास जामीनदाराला परतफेड करावी लागू शकते.","collateral":"हप्ते थकल्यास तारण मालमत्ता धोक्यात येऊ शकते.","early":"मुदतपूर्व परतफेडीवर शुल्क लागू शकते.","exclude":"काही परिस्थितींना विम्याचे संरक्षण मिळणार नाही.","minimum":"फक्त किमान रक्कम भरल्यास कर्ज आणि व्याज वाढू शकते.","data":"वैयक्तिक माहिती दुसऱ्या संस्थेला दिली जाऊ शकते."}}

GENERIC={
"en":{"purpose":"This document records financial information, rights, payments, or responsibilities.","meaning":"Read the amounts, dates, names, and conditions carefully before acting.","advice":"Confirm every amount and date with the issuing organisation.","question":"What action is required, by when, and what charges may apply?"},
"hi":{"purpose":"यह दस्तावेज़ वित्तीय जानकारी, अधिकार, भुगतान या जिम्मेदारियों का अभिलेख है।","meaning":"कोई कदम उठाने से पहले राशि, तारीख, नाम और शर्तें ध्यान से पढ़ें।","advice":"हर राशि और तारीख जारी करने वाली संस्था से मिलाएँ।","question":"मुझे क्या कदम कब तक उठाना है और कौन-से शुल्क लग सकते हैं?"},
"mr":{"purpose":"हा दस्तऐवज आर्थिक माहिती, हक्क, देयके किंवा जबाबदाऱ्यांचा अभिलेख आहे.","meaning":"कृती करण्यापूर्वी रक्कम, तारीख, नावे आणि अटी काळजीपूर्वक वाचा.","advice":"प्रत्येक रक्कम आणि तारीख दस्तऐवज देणाऱ्या संस्थेकडून तपासा.","question":"मला कोणती कृती कधीपर्यंत करायची आहे आणि कोणते शुल्क लागू शकते?"}}
SPECIFIC={
"bank_statement":{"en":("This records money entering and leaving your bank account.","Check deposits, withdrawals, charges, and the closing balance."),"hi":("यह आपके बैंक खाते में आई और गई राशि का अभिलेख है।","जमा, निकासी, शुल्क और अंतिम शेष राशि जाँचें।"),"mr":("हा तुमच्या बँक खात्यात आलेल्या आणि गेलेल्या पैशांचा अभिलेख आहे.","जमा, पैसे काढणे, शुल्क आणि अखेरची शिल्लक तपासा.")},
"loan_agreement":{"en":("This legal agreement sets the amount borrowed and repayment rules.","It may create a long-term payment duty and put assets or a guarantor at risk."),"hi":("यह उधार राशि और उसे लौटाने के नियमों वाला कानूनी समझौता है।","इससे लंबे समय की भुगतान जिम्मेदारी बन सकती है और संपत्ति या जमानतदार पर जोखिम आ सकता है।"),"mr":("हा कर्जाची रक्कम आणि परतफेडीचे नियम नमूद करणारा कायदेशीर करार आहे.","यामुळे दीर्घकाळ पैसे भरण्याची जबाबदारी येऊ शकते आणि मालमत्ता किंवा जामीनदार धोक्यात येऊ शकतो.")},
"insurance_policy":{"en":("This contract describes insurance protection in return for premium payments.","Claims depend on the cover, exclusions, waiting periods, and accurate information."),"hi":("यह बीमा किस्त के बदले मिलने वाली सुरक्षा का अनुबंध है।","दावा सुरक्षा, अपवाद, प्रतीक्षा अवधि और सही जानकारी पर निर्भर करता है।"),"mr":("हा विम्याच्या हप्त्याच्या बदल्यात मिळणाऱ्या संरक्षणाचा करार आहे.","दावा संरक्षण, अपवाद, प्रतीक्षा काळ आणि अचूक माहितीवर अवलंबून असतो.")},
"salary_slip":{"en":("This is a breakdown of work earnings and deductions.","It shows how gross earnings become the amount paid to you."),"hi":("यह काम से मिली कमाई और कटौतियों का विवरण है।","यह दिखाता है कि कुल कमाई में कटौती के बाद कितनी राशि मिली।"),"mr":("हा नोकरीतील कमाई आणि वजावटींचा तपशील आहे.","एकूण कमाईतून वजावट झाल्यानंतर किती वेतन मिळाले ते यात दिसते.")},
"utility_bill":{"en":("This is a bill for electricity, water, gas, or another service.","Check usage, amount payable, and the last payment date."),"hi":("यह बिजली, पानी, गैस या दूसरी सेवा का बिल है।","उपयोग, देय राशि और भुगतान की अंतिम तारीख जाँचें।"),"mr":("हे वीज, पाणी, गॅस किंवा इतर सेवेचे देयक आहे.","वापर, देय रक्कम आणि भरण्याची अंतिम तारीख तपासा.")}}

def extract_file(name,data):
    if len(data)>20*1024*1024: raise ValueError("too large")
    suffix=Path(name).suffix.lower()
    if suffix in {".txt",".csv"}: return data.decode("utf-8-sig",errors="replace")
    if suffix in {".png",".jpg",".jpeg"}: return ocr(Image.open(io.BytesIO(data)))
    if suffix==".pdf":
        from pypdf import PdfReader
        try: text="\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        except Exception: text=""
        if len(text.strip())>=80:return text
        import fitz
        pages=[]; doc=fitz.open(stream=data,filetype="pdf")
        for page in list(doc)[:12]: pages.append(ocr(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png")))))
        return "\n".join(pages)
    raise ValueError("unsupported")

def analyze(text,lang,kb):
    kind,confidence=classify(text,kb); info=GENERIC[lang]; purpose,meaning=SPECIFIC.get(kind,{}).get(lang,(info["purpose"],info["meaning"]))
    details=[]
    for key,patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match=re.search(pattern,text,re.I)
            if match:
                value=" ".join(match.group(1).split()).strip(" :-")
                if key=="account": value="•••• "+re.sub(r"\D","",value)[-4:]
                elif key=="interest": value+="%"
                elif key not in {"due_date"}: value="₹"+value
                details.append((LABELS[lang][key],value));break
    risks=[]
    for pattern,key in RISK_RULES:
        if re.search(pattern,text,re.I): risks.append(RISK[lang][key])
    matches=retrieve(text,kb,4)
    return {"type":kind,"confidence":confidence,"purpose":purpose,"meaning":meaning,"details":details[:8],"risks":risks[:6],"advice":[info["advice"]],"questions":[info["question"]],"matches":matches}

def safe(x):return html.escape(str(x))
def card(title,body):st.markdown(f'<section class="section"><h2>{safe(title)}</h2><p>{safe(body)}</p></section>',unsafe_allow_html=True)
def list_card(title,items,empty):
    rows="".join(f"<li>{safe(x)}</li>" for x in (items or [empty]));st.markdown(f'<section class="section"><h2>{safe(title)}</h2><ul>{rows}</ul></section>',unsafe_allow_html=True)

kb,kb_status=load_kb()
previous=LANGUAGES.get(st.session_state.get("lang","English"),"en")
language_name=st.selectbox(T[previous]["language"],list(LANGUAGES),key="lang")
lang=LANGUAGES[language_name];t=T[lang];brand="DhanDidi" if lang=="en" else "धनदीदी"
st.markdown(f'<header class="hero"><div class="brand">🌿 {brand}</div><h1>{safe(t["hero"])}</h1><p>{safe(t["hero_body"])}</p></header>',unsafe_allow_html=True)
st.markdown(f'<h2 style="color:#12304a;font-size:1.7rem">{safe(t["tag"])}</h2><p style="font-size:1.1rem">{safe(t["sub"])}</p><div class="privacy">{safe(t["privacy"])}</div><div class="status">● {safe(t["ready"] if kb_status=="ready" else t["fallback"])}</div>',unsafe_allow_html=True)
st.markdown(f'<section class="section"><h2>{safe(t["upload"])}</h2><p>{safe(t["formats"])}</p></section>',unsafe_allow_html=True)
uploaded=st.file_uploader(t["choose"],type=["pdf","png","jpg","jpeg","txt","csv"],label_visibility="collapsed")
if uploaded and st.button(t["analyze"],type="primary",use_container_width=True):
    try:
        with st.spinner(t["working"]):
            raw="\n".join(" ".join(line.split()) for line in extract_file(uploaded.name,uploaded.getvalue()).splitlines() if line.strip())
            if len(raw)<25:st.warning(t["unreadable"])
            else:st.session_state.result=(analyze(raw,lang,kb),raw,uploaded.name,lang)
    except Exception:st.error(t["error"])
saved=st.session_state.get("result")
if saved and uploaded and saved[2]==uploaded.name:
    result,raw,_,saved_lang=saved
    if saved_lang!=lang:result=analyze(raw,lang,kb);st.session_state.result=(result,raw,uploaded.name,lang)
    st.markdown(f'<section class="doc"><div class="doc-label">{safe(t["dtype"])}</div><div class="doc-type">{safe(DOC[lang][result["type"]])}</div><span class="pill">{safe(t["confidence"])}: {safe(t[result["confidence"]])}</span></section>',unsafe_allow_html=True)
    card(t["what"],result["purpose"]);card(t["means"],result["meaning"])
    if result["details"]:
        cells="".join(f'<div class="detail"><small>{safe(k)}</small><strong>{safe(v)}</strong></div>' for k,v in result["details"]);st.markdown(f'<section class="section"><h2>{safe(t["important"])}</h2><div class="detail-grid">{cells}</div></section>',unsafe_allow_html=True)
    else:card(t["important"],t["none"])
    list_card(t["careful"],result["risks"],t["norisk"]);list_card(t["advice"],result["advice"],"");list_card(t["questions"],result["questions"],"")
    card(t["reference"],t["refnote"].format(count=len(result["matches"])));st.info(t["note"])
    with st.expander(t["raw"]):st.text(raw[:12000])
    report="\n\n".join([t["dtype"]+"\n"+DOC[lang][result["type"]],t["what"]+"\n"+result["purpose"],t["means"]+"\n"+result["meaning"],t["careful"]+"\n"+"\n".join("• "+x for x in result["risks"]),t["disclaimer"]])
    st.download_button(t["download"],report,file_name="DhanDidi_explanation.txt",mime="text/plain")
st.markdown(f'<div class="footer">{safe(t["disclaimer"])}</div>',unsafe_allow_html=True)
