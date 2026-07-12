from dataset_kb import DatasetKnowledgeBase, ReferenceExample


def test_retrieval_prefers_relevant_reference() -> None:
    kb = DatasetKnowledgeBase(
        [
            ReferenceExample("bank_statement", "closing balance debit credit transaction account", "bank.jpg"),
            ReferenceExample("cheque", "pay bearer rupees signature cheque", "cheque.jpg"),
        ]
    )

    matches = kb.retrieve("account transaction debit closing balance", limit=1)

    assert matches[0].doc_type == "bank_statement"
    assert matches[0].similarity > 0


def test_type_scores_are_normalized() -> None:
    kb = DatasetKnowledgeBase([ReferenceExample("salary_slip", "salary gross pay net pay", "salary.jpg")])

    scores = kb.type_scores("salary net pay")

    assert scores == {"salary_slip": 1.0}
