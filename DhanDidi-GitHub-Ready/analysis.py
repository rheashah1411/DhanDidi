"""Hybrid document analysis: deterministic safety rules + dataset retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from dataset_kb import DatasetKnowledgeBase, Match


TYPE_KEYWORDS = {
    "bank_statement": {"bank statement": 8, "account statement": 8, "opening balance": 4, "closing balance": 5, "withdrawal": 2, "deposit": 2, "transaction": 2, "narration": 2},
    "cheque": {"pay to": 4, "payee": 4, "bearer": 4, "or order": 3, "rupees": 2, "cheque": 7, "micr": 3},
    "tax_document": {"form 16": 10, "income tax": 6, "tds": 5, "assessment year": 4, "tax deducted": 5, "pan": 2},
    "salary_slip": {"salary slip": 9, "payslip": 9, "basic salary": 4, "gross pay": 5, "net pay": 5, "provident fund": 3, "employee id": 2},
    "utility_bill": {"electricity bill": 9, "water bill": 9, "gas bill": 9, "consumer number": 5, "meter reading": 5, "units consumed": 4},
    "loan_agreement": {"loan agreement": 10, "borrower": 5, "lender": 5, "emi": 4, "loan amount": 4, "foreclosure": 4, "collateral": 4},
    "insurance_policy": {"insurance policy": 10, "policy number": 5, "sum assured": 5, "premium": 4, "nominee": 3, "insured": 3, "exclusion": 3},
    "scheme_form": {"government scheme": 8, "application form": 3, "beneficiary": 5, "eligibility": 4, "yojana": 5, "scheme form": 8},
    "credit_card_statement": {"credit card": 9, "minimum amount due": 6, "credit limit": 5, "payment due date": 5, "late payment": 4},
    "investment_document": {"mutual fund": 7, "investment": 4, "folio": 6, "nav": 5, "securities": 4, "demat": 5, "units allotted": 4},
    "pension_document": {"pension": 8, "ppo": 6, "annuity": 5, "retirement": 4, "life certificate": 5},
    "fixed_deposit": {"fixed deposit": 9, "term deposit": 8, "maturity amount": 5, "maturity date": 5, "deposit receipt": 5},
}

FIELD_PATTERNS = {
    "account_ending": [r"(?:account|a/c)\s*(?:no\.?|number)?\s*[:#-]?\s*([xX*\d -]{6,24})"],
    "loan_amount": [r"(?:loan amount|principal)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "interest_rate": [r"(?:interest|rate of interest)\s*(?:rate)?\s*[:@-]?\s*(\d{1,2}(?:\.\d+)?)\s*%"],
    "emi": [r"(?:emi|monthly instalment|monthly installment)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "premium": [r"(?:premium)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "sum_assured": [r"(?:sum assured|coverage amount)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "net_pay": [r"(?:net pay|net salary|take home)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "gross_pay": [r"(?:gross pay|gross salary)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "amount_due": [r"(?:total amount due|amount payable|amount due)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "minimum_due": [r"(?:minimum amount due|minimum due)\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "closing_balance": [r"(?:closing|available) balance\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "maturity_amount": [r"maturity amount\s*[:₹rs.inr ]+([\d,]+(?:\.\d{1,2})?)"],
    "policy_number": [r"policy\s*(?:no\.?|number)\s*[:#-]?\s*([a-z0-9/-]{4,24})"],
    "consumer_number": [r"consumer\s*(?:no\.?|number|id)\s*[:#-]?\s*([a-z0-9/-]{4,24})"],
    "employee_id": [r"employee\s*(?:id|no\.?|number)\s*[:#-]?\s*([a-z0-9/-]{3,20})"],
    "due_date": [r"(?:payment )?due date\s*[:#-]?\s*([0-3]?\d[./-][01]?\d[./-](?:\d{2}|\d{4}))"],
    "maturity_date": [r"maturity date\s*[:#-]?\s*([0-3]?\d[./-][01]?\d[./-](?:\d{2}|\d{4}))"],
}

FIELD_LABELS = {
    "en": {"account_ending": "Account number (protected)", "loan_amount": "Loan amount", "interest_rate": "Interest rate", "emi": "Monthly instalment", "premium": "Premium", "sum_assured": "Insurance cover", "net_pay": "Net pay", "gross_pay": "Gross pay", "amount_due": "Amount due", "minimum_due": "Minimum amount due", "closing_balance": "Closing balance", "maturity_amount": "Maturity amount", "policy_number": "Policy number", "consumer_number": "Consumer number", "employee_id": "Employee number", "due_date": "Due date", "maturity_date": "Maturity date", "dates": "Other important dates", "amounts": "Other amounts"},
    "hi": {"account_ending": "खाता संख्या (सुरक्षित)", "loan_amount": "ऋण राशि", "interest_rate": "ब्याज दर", "emi": "मासिक किस्त", "premium": "बीमा किस्त", "sum_assured": "बीमा सुरक्षा राशि", "net_pay": "प्राप्त वेतन", "gross_pay": "कुल वेतन", "amount_due": "देय राशि", "minimum_due": "न्यूनतम देय राशि", "closing_balance": "अंतिम शेष", "maturity_amount": "परिपक्वता राशि", "policy_number": "बीमा पॉलिसी संख्या", "consumer_number": "उपभोक्ता संख्या", "employee_id": "कर्मचारी संख्या", "due_date": "भुगतान की अंतिम तारीख", "maturity_date": "परिपक्वता तारीख", "dates": "अन्य महत्वपूर्ण तारीखें", "amounts": "अन्य राशियाँ"},
    "mr": {"account_ending": "खाते क्रमांक (सुरक्षित)", "loan_amount": "कर्जाची रक्कम", "interest_rate": "व्याजदर", "emi": "मासिक हप्ता", "premium": "विम्याचा हप्ता", "sum_assured": "विमा संरक्षण रक्कम", "net_pay": "हाती मिळणारे वेतन", "gross_pay": "एकूण वेतन", "amount_due": "देय रक्कम", "minimum_due": "किमान देय रक्कम", "closing_balance": "अखेरची शिल्लक", "maturity_amount": "मुदतपूर्ती रक्कम", "policy_number": "विमा पॉलिसी क्रमांक", "consumer_number": "ग्राहक क्रमांक", "employee_id": "कर्मचारी क्रमांक", "due_date": "भरण्याची अंतिम तारीख", "maturity_date": "मुदतपूर्ती तारीख", "dates": "इतर महत्त्वाच्या तारखा", "amounts": "इतर रकमा"},
}

RISK_RULES = [
    (r"(?:late|delay).{0,35}(?:fee|charge|penalt)|penalt.{0,20}(?:late|delay)", "late_fee", "medium"),
    (r"auto(?:matic)?\s*(?:debit|deduction)|standing instruction|nach mandate", "auto_debit", "medium"),
    (r"guarantor|jointly and severally", "guarantor", "high"),
    (r"collateral|hypothecat|mortgage|security interest", "collateral", "high"),
    (r"foreclosure|prepayment charge", "foreclosure", "medium"),
    (r"variable interest|floating rate|rate may (?:change|vary)", "variable_rate", "medium"),
    (r"exclusion|not covered|waiting period", "exclusion", "high"),
    (r"minimum amount due", "minimum_due", "medium"),
    (r"consent to share|share your (?:data|information)|third part", "data_consent", "medium"),
]

# Once the dataset-assisted classifier identifies a type, only relevant fields
# and warning clauses are prioritised. This is how reference similarity improves
# clause recognition and risk detection without treating the dataset as labelled
# legal advice.
TYPE_FIELDS = {
    "bank_statement": {"account_ending", "closing_balance", "dates", "amounts"},
    "cheque": {"account_ending", "dates", "amounts"},
    "tax_document": {"gross_pay", "employee_id", "dates", "amounts"},
    "salary_slip": {"employee_id", "gross_pay", "net_pay", "account_ending", "dates", "amounts"},
    "utility_bill": {"consumer_number", "amount_due", "due_date", "dates", "amounts"},
    "loan_agreement": {"loan_amount", "interest_rate", "emi", "due_date", "account_ending", "dates", "amounts"},
    "insurance_policy": {"policy_number", "premium", "sum_assured", "due_date", "dates", "amounts"},
    "credit_card_statement": {"account_ending", "amount_due", "minimum_due", "due_date", "dates", "amounts"},
    "fixed_deposit": {"interest_rate", "maturity_amount", "maturity_date", "account_ending", "dates", "amounts"},
}
TYPE_RISKS = {
    "bank_statement": {"auto_debit", "data_consent"},
    "cheque": {"data_consent"},
    "tax_document": {"data_consent"},
    "salary_slip": {"auto_debit", "data_consent"},
    "utility_bill": {"late_fee", "auto_debit", "data_consent"},
    "loan_agreement": {"late_fee", "auto_debit", "guarantor", "collateral", "foreclosure", "variable_rate", "data_consent"},
    "insurance_policy": {"auto_debit", "exclusion", "data_consent"},
    "scheme_form": {"data_consent"},
    "credit_card_statement": {"late_fee", "auto_debit", "minimum_due", "variable_rate", "data_consent"},
    "investment_document": {"auto_debit", "data_consent"},
    "pension_document": {"auto_debit", "data_consent"},
    "fixed_deposit": {"foreclosure", "data_consent"},
}

RISK_TEXT = {
    "en": {"late_fee": "A fee or penalty may apply if payment is late.", "auto_debit": "Money may be deducted automatically; check the amount and debit date.", "guarantor": "A guarantor may become responsible for repayment if the borrower does not pay.", "collateral": "An asset may be pledged and could be at risk if payments are missed.", "foreclosure": "A charge may apply if you repay the loan early.", "variable_rate": "The interest rate may change, so future instalments could increase.", "exclusion": "Some events or conditions may not be covered by this insurance.", "minimum_due": "Paying only the minimum can leave debt and add interest.", "data_consent": "The document may permit sharing personal information with another organisation."},
    "hi": {"late_fee": "देरी से भुगतान करने पर शुल्क या जुर्माना लग सकता है।", "auto_debit": "राशि अपने-आप कट सकती है; कटने वाली राशि और तारीख जाँचें।", "guarantor": "ऋण लेने वाला भुगतान न करे तो जमानतदार को भुगतान करना पड़ सकता है।", "collateral": "कोई संपत्ति सुरक्षा के रूप में रखी जा सकती है और किस्त न चुकाने पर वह खतरे में पड़ सकती है।", "foreclosure": "ऋण समय से पहले चुकाने पर शुल्क लग सकता है।", "variable_rate": "ब्याज दर बदल सकती है, इसलिए आगे की किस्त बढ़ सकती है।", "exclusion": "कुछ घटनाएँ या स्थितियाँ इस बीमा में शामिल नहीं हो सकतीं।", "minimum_due": "केवल न्यूनतम राशि चुकाने से कर्ज बाकी रह सकता है और ब्याज बढ़ सकता है।", "data_consent": "दस्तावेज़ आपकी निजी जानकारी किसी दूसरी संस्था से साझा करने की अनुमति दे सकता है।"},
    "mr": {"late_fee": "उशिरा पैसे भरल्यास शुल्क किंवा दंड लागू शकतो.", "auto_debit": "रक्कम आपोआप वजा होऊ शकते; रक्कम आणि वजावटीची तारीख तपासा.", "guarantor": "कर्जदाराने पैसे न भरल्यास जामीनदाराला परतफेड करावी लागू शकते.", "collateral": "एखादी मालमत्ता तारण असू शकते आणि हप्ते थकल्यास ती धोक्यात येऊ शकते.", "foreclosure": "कर्ज मुदतीपूर्वी फेडल्यास शुल्क लागू शकते.", "variable_rate": "व्याजदर बदलू शकतो, त्यामुळे पुढील हप्ते वाढू शकतात.", "exclusion": "काही घटना किंवा परिस्थितींना या विम्याचे संरक्षण मिळणार नाही.", "minimum_due": "फक्त किमान रक्कम भरल्यास कर्ज बाकी राहून व्याज वाढू शकते.", "data_consent": "दस्तऐवज तुमची वैयक्तिक माहिती दुसऱ्या संस्थेला देण्याची परवानगी देऊ शकतो."},
}

CONTENT = {
    "en": {
        "bank_statement": ("A record of money entering and leaving your bank account during a stated period.", "It helps you check deposits, withdrawals, charges, and the balance available to you.", "Check unfamiliar transactions and report them promptly.", "Is every transaction mine, and were any unexpected charges deducted?"),
        "cheque": ("A written instruction asking a bank to pay a stated amount from an account.", "The payee, amount, date, crossing, and signature decide how the cheque can be used.", "Confirm the payee and amount before signing; never sign a blank cheque.", "Are the payee, amount in words and figures, and date all correct?"),
        "tax_document": ("A record used to report income and tax deducted or paid.", "It helps you verify earnings, deductions, and tax details before filing a return.", "Match your name and tax identity number with official records.", "Do the income and tax-deduction figures match my records?"),
        "salary_slip": ("A monthly breakdown of your earnings and deductions from work.", "It shows how gross earnings become the amount paid to you after deductions.", "Compare deductions with your employment terms and bank credit.", "Are all deductions authorised and is the final pay correct?"),
        "utility_bill": ("A bill for a service such as electricity, water, or gas.", "It states your usage, amount payable, and the last date for payment.", "Check the meter reading and consumer number before paying.", "Does the meter reading match my meter and is any old balance included?"),
        "loan_agreement": ("A legal agreement setting the amount borrowed and the rules for repayment.", "It can create a long-term payment duty and may place assets or a guarantor at risk.", "Confirm the total repayment, interest, fees, and early-repayment rules before signing.", "What is the total amount I will repay, including every charge?"),
        "insurance_policy": ("A contract describing the protection an insurer promises in return for premium payments.", "Your claim depends on the cover, exclusions, waiting periods, and truthful information in the policy.", "Confirm the nominee, cover amount, exclusions, and renewal date.", "Which situations are excluded and what documents are needed for a claim?"),
        "scheme_form": ("An application or record for a government benefit or support scheme.", "Eligibility, documents, and deadlines determine whether you can receive the benefit.", "Use only official channels and do not pay an unauthorised agent.", "Am I eligible, which documents are required, and is there any official fee?"),
        "credit_card_statement": ("A monthly record of card spending, repayments, fees, and the amount due.", "You should pay by the due date; paying only the minimum can increase interest.", "Check unfamiliar purchases and aim to pay the full amount due.", "What interest applies if I do not pay the full amount?"),
        "investment_document": ("A record of an investment, its units or holdings, value, and applicable terms.", "Returns can change and past performance does not guarantee future gains.", "Verify ownership, fees, risk level, and withdrawal restrictions.", "What fees, risks, and withdrawal limits apply?"),
        "pension_document": ("A record concerning retirement income, contributions, or pension payments.", "It affects income you may receive after retirement and may include nominee details.", "Verify your pension number, nominee, bank details, and payment status.", "Are my service history, nominee, and bank details correct?"),
        "fixed_deposit": ("A record of money kept with a bank for a fixed period at an agreed rate.", "You receive the maturity amount if the deposit stays until the stated date; early withdrawal may reduce returns.", "Check the rate, maturity instruction, nominee, and early-withdrawal penalty.", "What amount will I receive at maturity and what happens if I withdraw early?"),
        "unknown": ("This appears to be a financial document, but its exact type is not clear enough.", "It may contain payment, account, tax, benefit, or contractual information that needs careful checking.", "Ask the issuing organisation to confirm the document type and purpose.", "Who issued this document, why was it sent, and do I need to act?"),
    },
    "hi": {
        "bank_statement": ("यह तय अवधि में आपके बैंक खाते में आई और गई राशि का अभिलेख है।", "इससे आप जमा, निकासी, शुल्क और उपलब्ध शेष राशि जाँच सकती हैं।", "अनजान लेन-देन जाँचें और उसकी सूचना तुरंत बैंक को दें।", "क्या हर लेन-देन मेरा है और क्या कोई अनपेक्षित शुल्क काटा गया है?"),
        "cheque": ("यह बैंक को खाते से लिखी हुई राशि चुकाने का निर्देश है।", "प्राप्तकर्ता, राशि, तारीख, रेखांकन और हस्ताक्षर तय करते हैं कि चेक का उपयोग कैसे होगा।", "हस्ताक्षर से पहले प्राप्तकर्ता और राशि जाँचें; खाली चेक पर कभी हस्ताक्षर न करें।", "क्या प्राप्तकर्ता, अंकों और शब्दों में राशि तथा तारीख सही हैं?"),
        "tax_document": ("यह आय और काटे या चुकाए गए कर का अभिलेख है।", "आयकर विवरणी भरने से पहले इससे कमाई, कटौती और कर की जानकारी जाँची जाती है।", "अपना नाम और स्थायी खाता संख्या सरकारी अभिलेख से मिलाएँ।", "क्या आय और काटे गए कर की राशि मेरे अभिलेख से मिलती है?"),
        "salary_slip": ("यह काम से मिली मासिक कमाई और कटौतियों का विवरण है।", "यह दिखाती है कि कुल कमाई में कटौती के बाद आपको कितनी राशि मिली।", "कटौतियों को नौकरी की शर्तों और बैंक में आई राशि से मिलाएँ।", "क्या सभी कटौतियाँ अधिकृत हैं और अंतिम वेतन सही है?"),
        "utility_bill": ("यह बिजली, पानी या गैस जैसी सेवा का बिल है।", "इसमें उपयोग, देय राशि और भुगतान की अंतिम तारीख होती है।", "भुगतान से पहले मीटर रीडिंग और उपभोक्ता संख्या जाँचें।", "क्या मीटर रीडिंग मेरे मीटर से मिलती है और क्या पुरानी बकाया राशि जोड़ी गई है?"),
        "loan_agreement": ("यह उधार ली गई राशि और उसे लौटाने के नियमों वाला कानूनी समझौता है।", "इससे लंबे समय तक भुगतान की जिम्मेदारी बन सकती है और संपत्ति या जमानतदार पर जोखिम आ सकता है।", "हस्ताक्षर से पहले कुल भुगतान, ब्याज, सभी शुल्क और समयपूर्व भुगतान के नियम समझें।", "सभी शुल्क मिलाकर मुझे कुल कितनी राशि चुकानी होगी?"),
        "insurance_policy": ("यह बीमा किस्त के बदले बीमा कंपनी द्वारा दी जाने वाली सुरक्षा का अनुबंध है।", "दावा सुरक्षा, अपवादों, प्रतीक्षा अवधि और दी गई सही जानकारी पर निर्भर करता है।", "नामित व्यक्ति, सुरक्षा राशि, अपवाद और नवीनीकरण तारीख जाँचें।", "कौन-सी स्थितियाँ शामिल नहीं हैं और दावा करने के लिए कौन-से दस्तावेज़ चाहिए?"),
        "scheme_form": ("यह सरकारी लाभ या सहायता योजना का आवेदन अथवा अभिलेख है।", "पात्रता, आवश्यक दस्तावेज़ और समय-सीमा से तय होता है कि आपको लाभ मिलेगा या नहीं।", "केवल सरकारी माध्यम अपनाएँ और अनधिकृत बिचौलिए को भुगतान न करें।", "क्या मैं पात्र हूँ, कौन-से दस्तावेज़ चाहिए और क्या कोई सरकारी शुल्क है?"),
        "credit_card_statement": ("यह कार्ड से किए खर्च, भुगतान, शुल्क और देय राशि का मासिक विवरण है।", "अंतिम तारीख तक भुगतान करें; केवल न्यूनतम राशि चुकाने से ब्याज बढ़ सकता है।", "अनजान खरीद जाँचें और पूरी देय राशि चुकाने का प्रयास करें।", "पूरी राशि न चुकाने पर कितना ब्याज लगेगा?"),
        "investment_document": ("यह निवेश, उसकी इकाइयों या हिस्सेदारी, मूल्य और शर्तों का अभिलेख है।", "लाभ बदल सकता है और पिछला प्रदर्शन भविष्य के लाभ की गारंटी नहीं देता।", "स्वामित्व, शुल्क, जोखिम स्तर और निकासी की पाबंदियाँ जाँचें।", "कौन-से शुल्क, जोखिम और निकासी की सीमाएँ लागू हैं?"),
        "pension_document": ("यह सेवानिवृत्ति आय, अंशदान या पेंशन भुगतान से जुड़ा अभिलेख है।", "यह सेवानिवृत्ति के बाद मिलने वाली आय को प्रभावित करता है और इसमें नामित व्यक्ति की जानकारी हो सकती है।", "पेंशन संख्या, नामित व्यक्ति, बैंक विवरण और भुगतान की स्थिति जाँचें।", "क्या मेरी सेवा अवधि, नामित व्यक्ति और बैंक विवरण सही हैं?"),
        "fixed_deposit": ("यह तय अवधि और ब्याज दर पर बैंक में रखी राशि का अभिलेख है।", "राशि तय तारीख तक जमा रहने पर परिपक्वता राशि मिलती है; पहले निकालने पर लाभ घट सकता है।", "ब्याज दर, परिपक्वता निर्देश, नामित व्यक्ति और समयपूर्व निकासी का जुर्माना जाँचें।", "परिपक्वता पर कितनी राशि मिलेगी और पहले निकालने पर क्या होगा?"),
        "unknown": ("यह वित्तीय दस्तावेज़ लगता है, पर इसका सही प्रकार पर्याप्त रूप से स्पष्ट नहीं है।", "इसमें भुगतान, खाते, कर, लाभ या अनुबंध की जानकारी हो सकती है, जिसे ध्यान से जाँचना चाहिए।", "जारी करने वाली संस्था से दस्तावेज़ का प्रकार और उद्देश्य पूछें।", "यह दस्तावेज़ किसने और क्यों भेजा है, और क्या मुझे कोई कदम उठाना है?"),
    },
    "mr": {
        "bank_statement": ("हा ठरावीक काळात तुमच्या बँक खात्यात आलेल्या आणि गेलेल्या पैशांचा अभिलेख आहे.", "यातून जमा, पैसे काढणे, शुल्क आणि उपलब्ध शिल्लक तपासता येते.", "अनोळखी व्यवहार तपासा आणि त्याची माहिती त्वरित बँकेला द्या.", "प्रत्येक व्यवहार माझाच आहे का आणि अनपेक्षित शुल्क वजा झाले आहे का?"),
        "cheque": ("हा बँकेला खात्यातून नमूद रक्कम देण्याचा लेखी आदेश आहे.", "प्राप्तकर्ता, रक्कम, तारीख, रेखांकन आणि सही यांवर धनादेशाचा वापर ठरतो.", "सही करण्यापूर्वी प्राप्तकर्ता आणि रक्कम तपासा; कोऱ्या धनादेशावर कधीही सही करू नका.", "प्राप्तकर्ता, अंक व शब्दांतील रक्कम आणि तारीख बरोबर आहेत का?"),
        "tax_document": ("हा उत्पन्न आणि कापलेल्या किंवा भरलेल्या प्राप्तिकराचा अभिलेख आहे.", "प्राप्तिकर विवरण भरण्यापूर्वी उत्पन्न, वजावट आणि कराची माहिती तपासण्यासाठी तो उपयोगी असतो.", "तुमचे नाव आणि कायम खाते क्रमांक शासकीय नोंदीशी जुळवा.", "उत्पन्न आणि कापलेल्या कराची रक्कम माझ्या नोंदीशी जुळते का?"),
        "salary_slip": ("हा नोकरीतील मासिक कमाई आणि वजावटींचा तपशील आहे.", "एकूण कमाईतून वजावट झाल्यानंतर तुम्हाला किती वेतन मिळाले ते यात दिसते.", "वजावटी नोकरीच्या अटींशी आणि बँकेत जमा रकमेशी जुळवा.", "सर्व वजावटी अधिकृत आहेत का आणि अंतिम वेतन बरोबर आहे का?"),
        "utility_bill": ("हे वीज, पाणी किंवा गॅससारख्या सेवेचे देयक आहे.", "यात वापर, देय रक्कम आणि भरण्याची अंतिम तारीख दिलेली असते.", "पैसे भरण्यापूर्वी मापक नोंद आणि ग्राहक क्रमांक तपासा.", "मापक नोंद माझ्या मापकाशी जुळते का आणि जुनी थकबाकी जोडली आहे का?"),
        "loan_agreement": ("हा घेतलेले कर्ज आणि परतफेडीचे नियम नमूद करणारा कायदेशीर करार आहे.", "यामुळे दीर्घकाळ पैसे भरण्याची जबाबदारी येऊ शकते आणि मालमत्ता किंवा जामीनदार धोक्यात येऊ शकतो.", "सही करण्यापूर्वी एकूण परतफेड, व्याज, सर्व शुल्क आणि मुदतपूर्व परतफेडीचे नियम समजून घ्या.", "सर्व शुल्कांसह मला एकूण किती रक्कम परत करावी लागेल?"),
        "insurance_policy": ("हा विम्याच्या हप्त्याच्या बदल्यात विमा कंपनी देत असलेल्या संरक्षणाचा करार आहे.", "दावा संरक्षण, अपवाद, प्रतीक्षा काळ आणि दिलेल्या अचूक माहितीवर अवलंबून असतो.", "नामनिर्देशित व्यक्ती, संरक्षण रक्कम, अपवाद आणि नूतनीकरण तारीख तपासा.", "कोणत्या परिस्थितींना संरक्षण नाही आणि दाव्यासाठी कोणते दस्तऐवज लागतील?"),
        "scheme_form": ("हा शासकीय लाभ किंवा मदत योजनेचा अर्ज अथवा अभिलेख आहे.", "पात्रता, आवश्यक कागदपत्रे आणि मुदत यांवर लाभ मिळणे अवलंबून असते.", "फक्त अधिकृत मार्ग वापरा आणि अनधिकृत मध्यस्थाला पैसे देऊ नका.", "मी पात्र आहे का, कोणती कागदपत्रे लागतील आणि अधिकृत शुल्क आहे का?"),
        "credit_card_statement": ("हा पतपत्रावरील खर्च, भरलेली रक्कम, शुल्क आणि देय रकमेचा मासिक तपशील आहे.", "अंतिम तारखेपर्यंत पैसे भरा; फक्त किमान रक्कम भरल्यास व्याज वाढू शकते.", "अनोळखी खरेदी तपासा आणि पूर्ण देय रक्कम भरण्याचा प्रयत्न करा.", "पूर्ण रक्कम न भरल्यास किती व्याज लागेल?"),
        "investment_document": ("हा गुंतवणूक, तिचे एकक किंवा धारण, मूल्य आणि अटींचा अभिलेख आहे.", "परतावा बदलू शकतो आणि मागील कामगिरी भविष्यातील नफ्याची हमी देत नाही.", "मालकी, शुल्क, जोखीम पातळी आणि पैसे काढण्यावरील मर्यादा तपासा.", "कोणते शुल्क, जोखीम आणि पैसे काढण्याच्या मर्यादा लागू आहेत?"),
        "pension_document": ("हा निवृत्तीनंतरचे उत्पन्न, अंशदान किंवा निवृत्तिवेतन देयकाचा अभिलेख आहे.", "याचा निवृत्तीनंतर मिळणाऱ्या उत्पन्नावर परिणाम होतो आणि यात नामनिर्देशित व्यक्तीचा तपशील असू शकतो.", "निवृत्तिवेतन क्रमांक, नामनिर्देशित व्यक्ती, बँक तपशील आणि देयक स्थिती तपासा.", "माझी सेवाकाल नोंद, नामनिर्देशित व्यक्ती आणि बँक तपशील बरोबर आहेत का?"),
        "fixed_deposit": ("हा ठरावीक काळ आणि व्याजदरासाठी बँकेत ठेवलेल्या पैशांचा अभिलेख आहे.", "ठरलेल्या तारखेपर्यंत ठेव कायम राहिल्यास मुदतपूर्ती रक्कम मिळते; आधी पैसे काढल्यास परतावा कमी होऊ शकतो.", "व्याजदर, मुदतपूर्ती सूचना, नामनिर्देशित व्यक्ती आणि मुदतपूर्व पैसे काढण्याचा दंड तपासा.", "मुदतपूर्तीला किती रक्कम मिळेल आणि आधी पैसे काढल्यास काय होईल?"),
        "unknown": ("हा आर्थिक दस्तऐवज दिसतो, पण त्याचा नेमका प्रकार पुरेसा स्पष्ट नाही.", "यात देयक, खाते, कर, लाभ किंवा कराराची माहिती असू शकते; ती काळजीपूर्वक तपासा.", "दस्तऐवज देणाऱ्या संस्थेकडून त्याचा प्रकार आणि उद्देश जाणून घ्या.", "हा दस्तऐवज कोणी आणि का पाठवला, आणि मला काही कृती करायची आहे का?"),
    },
}


@dataclass
class AnalysisResult:
    doc_type: str
    confidence: str
    purpose: str
    meaning: str
    details: list[tuple[str, str]]
    risks: list[str]
    recommendations: list[str]
    questions: list[str]
    matches: list[Match]


def _mask_identifier(value: str) -> str:
    compact = re.sub(r"\s", "", value)
    visible = re.sub(r"\D", "", compact)[-4:]
    return f"•••• {visible}" if visible else "••••"


def _extract_details(text: str, lang: str, doc_type: str) -> list[tuple[str, str]]:
    details: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key, patterns in FIELD_PATTERNS.items():
        relevant = TYPE_FIELDS.get(doc_type)
        if relevant and key not in relevant:
            continue
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = " ".join(match.group(1).split()).strip(" :-")
                if key == "account_ending":
                    value = _mask_identifier(value)
                elif key == "interest_rate":
                    value += "%"
                elif key in {"loan_amount", "emi", "premium", "sum_assured", "net_pay", "gross_pay", "amount_due", "minimum_due", "closing_balance", "maturity_amount"}:
                    value = f"₹{value}"
                item = (FIELD_LABELS[lang][key], value)
                if item not in seen:
                    details.append(item); seen.add(item)
                break
    if len(details) < 3:
        dates = list(dict.fromkeys(re.findall(r"\b[0-3]?\d[./-][01]?\d[./-](?:\d{2}|\d{4})\b", text)))[:3]
        amounts = list(dict.fromkeys(re.findall(r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?", text, re.I)))[:3]
        if dates:
            details.append((FIELD_LABELS[lang]["dates"], ", ".join(dates)))
        if amounts:
            details.append((FIELD_LABELS[lang]["amounts"], ", ".join(amounts)))
    return details[:8]


def _classify(text: str, kb: DatasetKnowledgeBase) -> tuple[str, str]:
    lower = text.lower()
    scores = {doc_type: sum(weight for phrase, weight in words.items() if phrase in lower) for doc_type, words in TYPE_KEYWORDS.items()}
    # The dataset affects classification here: real-example similarity contributes
    # up to six points, enough to disambiguate sparse scans but not overpower a
    # strong explicit phrase such as "loan agreement".
    for doc_type, similarity in kb.type_scores(text).items():
        scores[doc_type] = scores.get(doc_type, 0) + 6 * similarity
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_type, best = ordered[0] if ordered else ("unknown", 0)
    second = ordered[1][1] if len(ordered) > 1 else 0
    if best < 2.2:
        return "unknown", "low"
    margin = best - second
    return best_type, "high" if best >= 8 and margin >= 3 else "medium" if best >= 4 else "low"


def _sentences(text: str) -> Iterable[str]:
    return (part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if 15 <= len(part.strip()) <= 350)


def analyze_document(text: str, lang: str, kb: DatasetKnowledgeBase) -> AnalysisResult:
    doc_type, confidence = _classify(text, kb)
    matches = kb.retrieve(text, limit=4)
    purpose, meaning, recommendation, question = CONTENT[lang][doc_type]

    # Dataset retrieval also chooses the most relevant document template above.
    # Key fields and risk clauses remain conservative regex checks; this prevents
    # a visually similar reference from inventing values not present in the upload.
    risks: list[str] = []
    allowed_risks = TYPE_RISKS.get(doc_type, {key for _, key, _ in RISK_RULES})
    for sentence in _sentences(text):
        for pattern, risk_key, _severity in RISK_RULES:
            if risk_key in allowed_risks and re.search(pattern, sentence, re.I) and RISK_TEXT[lang][risk_key] not in risks:
                risks.append(RISK_TEXT[lang][risk_key])

    return AnalysisResult(
        doc_type=doc_type,
        confidence=confidence,
        purpose=purpose,
        meaning=meaning,
        details=_extract_details(text, lang, doc_type),
        risks=risks[:6],
        recommendations=[recommendation],
        questions=[question],
        matches=matches,
    )
