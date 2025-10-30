# CityBudget RAG System - Working Checkpoint

**Date:** January 2025  
**Status:** ✅ WORKING  
**Version:** Production Ready

## 🎯 System Overview

This is a fully functional Retrieval-Augmented Generation (RAG) system for querying city budget PDFs using natural language. The system is production-ready with comprehensive error handling, multiple deployment options, and a modern web interface.

## 🏗️ Architecture

### Core Components
- **Main System:** `main.py` - CityBudgetRAG orchestrator class
- **PDF Processing:** `src/pdf_processor.py` - OCR + text extraction with PyMuPDF, Tesseract, Camelot
- **Text Processing:** `src/text_processor.py` - LangChain chunking and cleaning
- **Embeddings:** `src/embeddings.py` - OpenAI text-embedding-3-small
- **Vector Store:** `src/vector_store.py` - Pinecone + ChromaDB support
- **Query Engine:** `src/query_engine.py` - GPT-4 Turbo RAG processing
- **Configuration:** `src/config.py` - Environment-based config management

### API & Web Interface
- **Backend:** `api.py` - FastAPI REST API with document upload/query endpoints
- **Frontend:** `web/web_app.py` + `static/index.html` - Modern Flask web interface
- **CLI:** `cli.py` - Command-line interface for batch operations

## 🤖 AI Models Used

1. **GPT-4o-mini** - Main LLM for answer generation (configurable, cheaper alternative to GPT-4)
2. **text-embedding-3-small** - Vector embeddings for semantic search (configurable to text-embedding-3-large)
3. **GPT-4o-mini** - Metadata extraction during document upload (configurable)

## 🚀 Key Features

### Document Processing
- ✅ PDF text extraction with OCR fallback
- ✅ Table extraction using Camelot
- ✅ Intelligent text chunking with overlap
- ✅ Automatic metadata extraction (city, fiscal year)
- ✅ Document isolation using document_id

### Vector Search
- ✅ OpenAI embeddings (text-embedding-3-small)
- ✅ Pinecone (primary) + ChromaDB (fallback) support
- ✅ Document-specific filtering
- ✅ Semantic similarity search

### Query Processing
- ✅ GPT-4 Turbo for answer generation
- ✅ Context-aware responses with source citations
- ✅ Redis caching for performance
- ✅ Multi-document support

### Web Interface
- ✅ Modern, responsive design
- ✅ Drag-and-drop PDF upload
- ✅ Real-time query interface
- ✅ Example questions and source citations
- ✅ Tabbed navigation (Ask/Upload)

## 🐳 Deployment Options

### Docker (Recommended)
```bash
docker-compose up --build
# API: http://localhost:8000
# Frontend: http://localhost:5000
```

### Local Development
```bash
# Backend
uvicorn api:app --reload --port 8000

# Frontend
python web/web_app.py
```

### CLI Usage
```bash
python cli.py ingest path/to/budget.pdf --city "Spokane" --year "2025"
python cli.py query "What is the total budget?"
```

## 📁 Project Structure
```
CityBudget_RAG_GIT/
├── api.py                 # FastAPI backend
├── main.py               # Core RAG system
├── cli.py                # Command-line interface
├── src/                  # Core modules
│   ├── config.py         # Configuration management
│   ├── pdf_processor.py  # PDF processing & OCR
│   ├── text_processor.py # Text cleaning & chunking
│   ├── embeddings.py     # OpenAI embeddings
│   ├── vector_store.py   # Vector database abstraction
│   └── query_engine.py   # RAG query processing
├── web/                  # Flask frontend
├── static/               # Web assets
├── data/pdfs/            # Uploaded documents
├── tests/                # Test suite
├── docker-compose.yml    # Docker configuration
└── requirements.txt      # Python dependencies
```

## ⚙️ Environment Configuration

Required environment variables:
```bash
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

## 🧪 Testing

- Unit tests in `tests/` directory
- API tests for FastAPI endpoints
- Text processor validation tests
- Health check endpoints

## 📊 Performance Features

- Redis caching for query results
- Batch processing for embeddings
- Document-specific vector filtering
- Efficient chunking with overlap
- OCR fallback for scanned documents

## 🔒 Security & Production

- Environment-based configuration
- Production config in `config/production.py`
- API key management
- Error handling and logging
- Docker containerization

## ✅ Verification Checklist

- [x] PDF processing with OCR fallback
- [x] Vector store integration (Pinecone + ChromaDB)
- [x] OpenAI API integration (GPT-4 + embeddings)
- [x] Web interface functionality
- [x] Document upload and processing
- [x] Query processing with source citations
- [x] Docker deployment ready
- [x] CLI interface working
- [x] Error handling implemented
- [x] Configuration management
- [x] Multi-document support
- [x] Redis caching
- [x] Test suite included

## 🎯 Use Cases

- Municipal budget analysis
- Financial document querying
- Government transparency tools
- Budget comparison across cities
- Public finance education
- Policy research and analysis

---

**Note:** This checkpoint represents a fully functional, production-ready RAG system for city budget analysis. All core features are implemented and tested. The system is ready for deployment and use.
