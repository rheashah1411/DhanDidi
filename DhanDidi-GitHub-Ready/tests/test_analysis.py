from analysis import analyze_document
from dataset_kb import DatasetKnowledgeBase, ReferenceExample


def knowledge_base() -> DatasetKnowledgeBase:
    return DatasetKnowledgeBase(
        [
            ReferenceExample(
                "bank_statement",
                "account statement opening balance closing balance debit credit transaction",
                "Bank Statement/example.jpg",
            ),
            ReferenceExample(
                "salary_slip",
                "salary slip employee basic pay gross pay net pay provident fund deduction",
                "Salary Slip/example.jpg",
            ),
        ]
    )


def test_bank_statement_classification_and_masking() -> None:
    result = analyze_document(
        "BANK ACCOUNT STATEMENT Account No: 1234567890 Closing Balance: INR 12,450.50 debit credit transaction",
        "en",
        knowledge_base(),
    )

    assert result.doc_type == "bank_statement"
    assert result.confidence == "high"
    assert any(value == "•••• 7890" for _, value in result.details)
    assert all("1234567890" not in value for _, value in result.details)


def test_loan_context_extracts_risks_and_values() -> None:
    result = analyze_document(
        "LOAN AGREEMENT. Borrower EMI: Rs 5,000. Interest rate: 18%. Late payment penalty applies. Collateral is required.",
        "en",
        knowledge_base(),
    )

    assert result.doc_type == "loan_agreement"
    assert ("Interest rate", "18%") in result.details
    assert len(result.risks) == 2


def test_localized_results_are_devanagari() -> None:
    sample = "INSURANCE POLICY Policy Number: AB/123 Premium: INR 9,000. Exclusions apply."

    hindi = analyze_document(sample, "hi", knowledge_base())
    marathi = analyze_document(sample, "mr", knowledge_base())

    assert hindi.purpose.startswith("यह")
    assert marathi.purpose.startswith("हा")
    assert hindi.risks and marathi.risks
