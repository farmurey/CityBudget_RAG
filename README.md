# 📊 City Budget Query System

An end-to-end Retrieval-Augmented Generation (RAG) system that enables natural language querying of city budget PDFs using OpenAI's GPT models, vector search, and OCR-enhanced document parsing. Features a FastAPI backend, Flask-based frontend, and supports Pinecone or ChromaDB as the vector store.

---

## 🚀 Features

- ✅ Upload and parse scanned or digital PDFs with OCR fallback
- ✅ Extract text and tables with PyMuPDF, Tesseract, and Camelot
- ✅ Clean and chunk content using LangChain's RecursiveCharacterTextSplitter
- ✅ Generate embeddings using OpenAI’s `text-embedding-3-small`
- ✅ Store and retrieve chunks with Pinecone or ChromaDB
- ✅ Run semantic search + prompt-augmented LLM answers
- ✅ Redis caching for repeat queries
- ✅ Full-stack: FastAPI (API), Flask (frontend), Docker-ready

---

## 🧠 Architecture Overview

```plaintext
PDFs → PDFProcessor (OCR/Text/Table) 
     → TextProcessor (clean/chunk)
     → EmbeddingGenerator (OpenAI)
     → VectorStore (Pinecone / ChromaDB)
     → QueryEngine (OpenAI GPT)
     → API Response

🧾 Folder Structure
city-budget-query/
├── api.py                 # FastAPI backend
├── web/web_app.py         # Flask frontend
├── main.py                # CLI runner / core pipeline
├── src/
│   ├── config.py          # Loads env vars via dotenv
│   ├── pdf_processor.py   # OCR + table extractor
│   ├── text_processor.py  # Chunking and cleaning
│   ├── embeddings.py      # OpenAI embedding calls
│   ├── query_engine.py    # RAG core logic
│   └── vector_store.py    # Pinecone / Chroma support
├── static/                # Serves HTML page
├── templates/             # Flask template
├── data/pdfs              # Uploaded budget PDFs
├── data/processed         # Intermediate processed content
├── docker-compose.yml     # Docker + Redis setup
├── requirements.txt       # Python dependencies
├── .env                   # API keys and settings
└── README.md
```
## ⚙️ Environment Configuration (.env)
```
Create a .env file in the project root:
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-west1-gcp
REDIS_HOST=localhost
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small  # Options: text-embedding-3-small, text-embedding-3-large
LLM_MODEL=gpt-4o-mini  # Options: gpt-4o-mini, gpt-4o, gpt-4-turbo
METADATA_EXTRACTION_MODEL=gpt-4o-mini  # Options: gpt-4o-mini, gpt-4o
VECTOR_DB_INDEX=city-budgets
```
## 🐳 Docker Setup
```
docker-compose up --build

API: http://localhost:8000

Frontend: http://localhost:5000

```
## 🔧 Local Development
```
1. Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Run the FastAPI backend
uvicorn api:app --reload --port 8000

3. (Optional) Run the Flask web app
python web/web_app.py
```
## 🧠 Powered By
```
OpenAI GPT-4 Turbo

Pinecone / ChromaDB

Tesseract OCR

Camelot PDF Tables

FastAPI

Flask

Redis
```
## 🙌 Acknowledgments
```
This project was built to make city budgets more accessible, understandable, and transparent through the power of LLMs and open-source AI.
```
