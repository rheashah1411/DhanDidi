from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import cgi
import re


LANGUAGES = {
    "en": {
        "brand": "DhanDidi",
        "title": "Namaste, upload your bank statement.",
        "subtitle": "Choose your language and upload a financial document. DhanDidi will explain the important details simply.",
        "language_label": "Choose your language",
        "upload_label": "Upload document",
        "button_text": "Read Document",
        "user_message": "I need help understanding this financial document.",
        "hello": "Namaste. I am DhanDidi. I found these important details.",
        "key_details": "Key details I found:",
        "simple_words": "Simple meaning of important words:",
        "risk_flags": "Things to be careful about:",
    },
    "hi": {
        "brand": "धनदीदी",
        "title": "नमस्ते, अपना बैंक स्टेटमेंट अपलोड करें।",
        "subtitle": "अपनी भाषा चुनें और दस्तावेज़ अपलोड करें। धनदीदी जरूरी जानकारी आसान भाषा में समझाएगी।",
        "language_label": "अपनी भाषा चुनें",
        "upload_label": "दस्तावेज़ अपलोड करें",
        "button_text": "दस्तावेज़ पढ़ें",
        "user_message": "मुझे यह वित्तीय दस्तावेज़ समझने में मदद चाहिए।",
        "hello": "नमस्ते। मैं धनदीदी हूं। मुझे ये जरूरी बातें मिलीं।",
        "key_details": "मिली हुई मुख्य जानकारी:",
        "simple_words": "जरूरी शब्दों का आसान मतलब:",
        "risk_flags": "इन बातों पर ध्यान दें:",
    },
    "mr": {
        "brand": "धनदीदी",
        "title": "नमस्कार, तुमचे बँक स्टेटमेंट अपलोड करा।",
        "subtitle": "तुमची भाषा निवडा आणि दस्तऐवज अपलोड करा. धनदीदी महत्वाची माहिती सोप्या भाषेत समजावेल.",
        "language_label": "तुमची भाषा निवडा",
        "upload_label": "दस्तऐवज अपलोड करा",
        "button_text": "दस्तऐवज वाचा",
        "user_message": "मला हा आर्थिक दस्तऐवज समजून घ्यायला मदत हवी आहे.",
        "hello": "नमस्कार। मी धनदीदी आहे। मला या महत्वाच्या गोष्टी सापडल्या.",
        "key_details": "मिळालेली मुख्य माहिती:",
        "simple_words": "महत्वाच्या शब्दांचा सोपा अर्थ:",
        "risk_flags": "या गोष्टींकडे लक्ष द्या:",
    }
}


def find_money(text):
    amounts = re.findall(r"(?:Rs\.?|INR|₹)?\s?\d[\d,]*(?:\.\d{1,2})?", text)
    return amounts[:8]


def find_dates(text):
    dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    return dates[:8]


def explain_terms(text, language):
    text = text.lower()
    explanations = []

    if "emi" in text or "loan" in text:
        if language == "hi":
            explanations.append("EMI मतलब loan की हर महीने कटने वाली किस्त।")
        elif language == "mr":
            explanations.append("EMI म्हणजे loan ची दर महिन्याला भरायची किस्त.")
        else:
            explanations.append("EMI means a fixed loan payment taken every month.")

    if "debit" in text or "withdrawal" in text:
        if language == "hi":
            explanations.append("Debit मतलब खाते से पैसा बाहर गया।")
        elif language == "mr":
            explanations.append("Debit म्हणजे खात्यातून पैसे गेले.")
        else:
            explanations.append("Debit means money went out of the account.")

    if "credit" in text or "deposit" in text:
        if language == "hi":
            explanations.append("Credit मतलब खाते में पैसा आया।")
        elif language == "mr":
            explanations.append("Credit म्हणजे खात्यात पैसे आले.")
        else:
            explanations.append("Credit means money came into the account.")

    if "interest" in text:
        if language == "hi":
            explanations.append("Interest मतलब ब्याज, यानी extra पैसा जो loan पर देना पड़ सकता है।")
        elif language == "mr":
            explanations.append("Interest म्हणजे व्याज, loan वर द्यायचे extra पैसे.")
        else:
            explanations.append("Interest means extra money paid on a loan or earned on savings.")

    return explanations


def find_risks(text, language):
    text = text.lower()
    risks = []

    if "penalty" in text or "fine" in text or "charge" in text or "fee" in text:
        if language == "hi":
            risks.append("Charges या penalty दिख रही है। बैंक से पूछें कि यह क्यों कटी।")
        elif language == "mr":
            risks.append("Charges किंवा penalty दिसत आहे. ती का कापली ते बँकेला विचारा.")
        else:
            risks.append("A charge, fee, or penalty appears. Ask why it was deducted.")

    if "emi" in text or "loan" in text:
        if language == "hi":
            risks.append("Loan या EMI कटौती दिख रही है। Amount और date सही है या नहीं जांचें।")
        elif language == "mr":
            risks.append("Loan किंवा EMI deduction दिसत आहे. Amount आणि date बरोबर आहे का तपासा.")
        else:
            risks.append("A loan or EMI deduction appears. Check the amount and date.")

    if "minimum balance" in text:
        if language == "hi":
            risks.append("Minimum balance rule दिख रहा है। कम balance होने पर fee लग सकती है।")
        elif language == "mr":
            risks.append("Minimum balance rule दिसत आहे. कमी balance असेल तर fee लागू शकते.")
        else:
            risks.append("Minimum balance rule appears. A fee may apply if balance is too low.")

    if not risks:
        if language == "hi":
            risks.append("कोई बड़ा warning sign नहीं मिला, लेकिन अनजान transactions जरूर जांचें।")
        elif language == "mr":
            risks.append("मोठा warning sign दिसला नाही, पण अनोळखी transactions तपासा.")
        else:
            risks.append("No big warning sign found, but check unknown transactions carefully.")

    return risks


def make_result(text, language):
    labels = LANGUAGES[language]
    money = find_money(text)
    dates = find_dates(text)
    terms = explain_terms(text, language)
    risks = find_risks(text, language)

    opening_balance = money[0] if len(money) > 0 else "Not found"
    closing_balance = money[-1] if len(money) > 0 else "Not found"

    start_date = dates[0] if len(dates) > 0 else "Not found"
    end_date = dates[-1] if len(dates) > 0 else "Not found"

    text_lower = text.lower()

    has_salary = "salary" in text_lower
    has_scheme = "scheme" in text_lower or "government" in text_lower
    has_emi = "emi" in text_lower or "loan" in text_lower
    has_medical = "medical" in text_lower or "hospital" in text_lower

    html = ""

    html += f"""
    <div class="message">
      This appears to be a bank statement showing the money that entered and left your bank account.
      <br><br>
      You can use this document to:
      <ul>
        <li>Check whether payments were made successfully.</li>
        <li>Monitor your income and expenses.</li>
        <li>Keep track of your account balance.</li>
      </ul>
    </div>
    """

    html += f"""
    <div class="message">
      <b>📌 The most important information</b>
      <br><br>
      <b>Statement Period</b><br>
      {start_date} – {end_date}
      <br><br>
      <b>Opening Balance</b><br>
      {opening_balance}
      <br><br>
      <b>Closing Balance</b><br>
      {closing_balance}
      <br><br>
      ⚠️ Your balance may have changed during this period. Please check if the closing balance looks correct.
    </div>
    """

    html += """
    <div class="message">
      <b>💡 What happened?</b>
      <br><br>
      During this period:
      <ul>
    """

    if has_salary:
        html += "<li>✅ Money was added to your account through your salary.</li>"

    if has_scheme:
        html += "<li>✅ You received money from a government scheme or benefit.</li>"

    if has_emi:
        html += "<li>⚠️ A loan payment or EMI may have been deducted automatically.</li>"

    if has_medical:
        html += "<li>⚠️ A medical payment was found. This may have reduced your balance.</li>"

    if not has_salary and not has_scheme and not has_emi and not has_medical:
        html += "<li>I found money amounts and dates, but no clear salary, EMI, scheme, or medical keywords.</li>"

    html += """
      </ul>
    </div>
    """

    html += """
    <div class="message">
      <b>📖 What these words mean</b>
      <br><br>
      <b>EMI</b><br>
      A fixed payment made every month to repay a loan.
      <br><br>
      <b>Debit</b><br>
      Money leaving your account.
      <br><br>
      <b>Credit</b><br>
      Money entering your account.
      <br><br>
      <b>Closing Balance</b><br>
      The amount left in your account after all transactions.
    </div>
    """

    html += f"""
    <div class="message warning">
      <b>⚠️ Things you should check</b>
      <ul>
    """

    for risk in risks:
        html += f"<li>{risk}</li>"

    html += """
        <li>Check that your salary or income was deposited correctly.</li>
        <li>Make sure you recognize all large payments.</li>
        <li>Keep enough balance before your next EMI or important payment.</li>
      </ul>
    </div>
    """

    html += """
    <div class="message">
      <b>🤖 AI Advice</b>
      <br><br>
      Based on this statement:
      <ul>
        <li>Keep at least one month's EMI in your account if possible.</li>
        <li>If you do not recognize any payment, contact your bank.</li>
        <li>Save this statement because it may be needed as proof of income.</li>
      </ul>
    </div>
    """

    if "penalty" in text_lower or "fine" in text_lower or "unknown" in text_lower:
        html += """
        <div class="message warning">
          <b>🌟 Confidence Meter</b>
          <br><br>
          🔴 There may be one transaction or charge that needs checking.
        </div>
        """
    else:
        html += """
        <div class="message">
          <b>🌟 Confidence Meter</b>
          <br><br>
          🟢 No obviously suspicious transaction detected, but still review unknown payments carefully.
        </div>
        """

    return html

def load_page(language="en", result=""):
    labels = LANGUAGES[language]

    with open("index.html", "r", encoding="utf-8") as file:
        page = file.read()

    for key, value in labels.items():
        page = page.replace("{{ " + key + " }}", value)

    page = page.replace("{{ en_selected }}", "selected" if language == "en" else "")
    page = page.replace("{{ hi_selected }}", "selected" if language == "hi" else "")
    page = page.replace("{{ mr_selected }}", "selected" if language == "mr" else "")

    if result == "":
        result = f"<div class='message'>{labels['hello']} Upload a document to begin.</div>"

    page = page.replace("{{ result }}", result)
    return page


class DhanDidiServer(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        language = query.get("language", ["en"])[0]

        if language not in LANGUAGES:
            language = "en"

        page = load_page(language)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"],
            }
        )

        language = form.getvalue("language", "en")
        uploaded_file = form["document"]

        file_data = uploaded_file.file.read()
        text = file_data.decode("utf-8", errors="ignore")

        result = make_result(text, language)
        page = load_page(language, result)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))


server = HTTPServer(("localhost", 8000), DhanDidiServer)
print("DhanDidi is running!")
print("Open this link: http://localhost:8000")
server.serve_forever()
