# DhanDidi · धनदीदी

DhanDidi is an accessible Streamlit assistant that explains financial documents in English, Hindi, and Marathi. It combines OCR, conservative document rules, and retrieval from the [Personal Financial Dataset for India](https://www.kaggle.com/datasets/mehaksingal/personal-financial-dataset-for-india/data).

> DhanDidi is an educational document-explanation tool. It is not legal, investment, or financial advice.

## Features

- PDF, scanned PDF, PNG, JPG, JPEG, TXT, and CSV uploads
- OCR with English, Hindi, and Marathi Tesseract language support
- Dataset-assisted document classification and similarity retrieval
- Bank statement, cheque, Form 16, salary slip, utility bill, loan, insurance, scheme, card, investment, pension, and fixed-deposit contexts
- Type-specific key information and warning-clause detection
- Fully localized English, Hindi, and Marathi explanations
- Protected account-number display and downloadable text reports
- Responsive, high-contrast Streamlit interface
- Safe offline fallback if Kaggle is temporarily unavailable

## Local setup

Requirements: Python 3.11 and Tesseract OCR.

On macOS:

```bash
brew install tesseract tesseract-lang
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. The first run downloads the public Kaggle dataset and writes a compact retrieval index to `.cache/`. Later starts reuse the index.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, choose **Create app** and select the repository.
3. Set the entry point to `app.py`.
4. Choose Python 3.11 if the deployment settings offer a version selector.
5. Deploy. `requirements.txt`, `packages.txt`, and `.streamlit/config.toml` are detected automatically.

The dataset is public, so Kaggle credentials are not normally required. On an ephemeral instance, the reference index may be rebuilt after a restart.

## Run with Docker

```bash
docker compose up --build
```

The image build downloads the dataset, builds the compact reference index, and deletes the raw Kaggle images. The container serves the application on `http://localhost:8501` and includes a health check.

## How the dataset improves analysis

1. `app.py` loads one process-wide knowledge base with `st.cache_resource`.
2. `dataset_kb.py` uses the Kaggle identifier defined in `dataset.txt`, samples every labelled document class, extracts reference text with OCR, and stores a compact index.
3. Uploaded text is compared with those reference examples using weighted token similarity.
4. Reference similarity contributes to document-type confidence and chooses type-appropriate terminology, extraction fields, clause checks, warnings, and explanation templates.
5. Exact values and warnings must still occur in the uploaded document. Reference documents never inject names, amounts, or dates into a result.

The Kaggle collection currently contains bank statements, cheques, Form 16 documents, salary slips, and utility bills. Broader document coverage uses conservative domain rules alongside the retrieval layer.

## Project structure

```text
app.py                 Streamlit interface and report rendering
analysis.py            Hybrid classification, extraction, risks, explanations
dataset_kb.py          Kaggle download, OCR indexing, and retrieval
document_reader.py     PDF, image, text, and CSV extraction
translations.py        English, Hindi, and Marathi interface content
styles.py              Accessible responsive visual system
tests/                 Unit and Streamlit smoke tests
.github/workflows/     GitHub Actions continuous integration
Dockerfile             Production container image
packages.txt           Streamlit Cloud system packages
```

## Tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

GitHub Actions runs syntax checks, correctness-focused linting, unit tests, and a Streamlit startup/language-switch test on every pull request.

## Privacy and data handling

- Uploaded documents are processed in memory and are not intentionally written to disk.
- Account identifiers displayed in extracted results are masked.
- Do not upload real financial documents to public demo deployments unless you trust the operator.
- Never attach unredacted financial documents to GitHub issues.
- `.gitignore` and `.dockerignore` exclude downloaded dataset files, caches, secrets, and local environments.

See [SECURITY.md](SECURITY.md) for deployment responsibilities and vulnerability reporting.

## Dataset and licensing

Application source code is available under the [MIT License](LICENSE). The Kaggle dataset is downloaded separately at runtime and remains governed by the license and terms shown on its Kaggle page; it is not redistributed by this repository.

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
