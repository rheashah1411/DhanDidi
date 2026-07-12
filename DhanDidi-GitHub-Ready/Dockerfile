FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DHANDIDI_CACHE_DIR=/app/.cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Download the public Kaggle data and retain only DhanDidi's compact OCR index.
# This makes container startup fast without shipping the raw financial images.
RUN python -c "from dataset_kb import load_knowledge_base; kb=load_knowledge_base(); assert kb.status == 'ready', kb.status" \
    && rm -rf /root/.cache/kagglehub /app/.cache/personal-financial-dataset-for-india /app/.cache/dataset.zip

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
