from fastapi import FastAPI, UploadFile, File, HTTPException
from starlette.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import shutil
from pathlib import Path
import uuid
import re
from datetime import datetime
import logging

from src.config import Config
from main import CityBudgetRAG, clean_city_name

# Set up logger
logger = logging.getLogger(__name__)

app = FastAPI(title="City Budget RAG API")
app.mount("/static", StaticFiles(directory="static"), name="static")

config = Config()
rag_system = CityBudgetRAG(config)
current_document = None

async def extract_metadata_with_ai(text_content: str, openai_api_key: str, model: str = "gpt-4o-mini") -> tuple[str, str]:
    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)
    sample_text = text_content[:3000]
    prompt = f"""Analyze this government budget document and extract:
1. The city name (just the city name, not \"City of X\")
2. The fiscal year (in format YYYY-YY or YYYY-YYYY)
If you can't find this information, respond with \"Unknown\" for that field.
Document text:
{sample_text}
Respond in this exact format:
City: [city name]
Fiscal Year: [fiscal year]"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at extracting information from government documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        result = response.choices[0].message.content
        city_match = re.search(r'City:\s*(.+)', result)
        fy_match = re.search(r'Fiscal Year:\s*(.+)', result)
        city_name = city_match.group(1).strip() if city_match else "Unknown"
        fiscal_year = fy_match.group(1).strip() if fy_match else "Unknown"
        return city_name, fiscal_year
    except Exception as e:
        logger.error(f"Error extracting metadata with AI: {e}")
        return "Unknown", "Unknown"

def extract_metadata_from_content(text_content: str) -> tuple[str, str]:
    city_patterns = [r'City of ([A-Za-z\s]+?)(?:\n|Budget|Fiscal)', r'([A-Za-z\s]+?) City', r'Municipality of ([A-Za-z\s]+)']
    fiscal_year_patterns = [r'FY\s*(\d{4}[-/]\d{2,4})', r'Fiscal Year\s*(\d{4}[-/]\d{2,4})', r'Budget\s*(\d{4}[-/]\d{2,4})', r'(\d{4}[-/]\d{2,4})\s*Budget']
    city_name, fiscal_year = "Unknown", "Unknown"
    for pattern in city_patterns:
        match = re.search(pattern, text_content[:5000], re.IGNORECASE)
        if match:
            city_name = match.group(1).strip()
            break
    for pattern in fiscal_year_patterns:
        match = re.search(pattern, text_content[:5000], re.IGNORECASE)
        if match:
            fiscal_year = match.group(1).strip()
            break
    return city_name, fiscal_year

class Query(BaseModel):
    question: str
    use_cache: bool = True
    city_name: Optional[str] = None  # Kept for backward compatibility

class IngestResponse(BaseModel):
    status: str
    file_id: str
    file_name: str
    chunks_processed: int
    pages_processed: int
    city_name: str
    fiscal_year: str
    document_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: list
    timestamp: str
    metadata: Dict[str, Any]

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/api/documents")
async def list_documents():
    if current_document:
        return [current_document]
    return []

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    global current_document
    city_name, fiscal_year = "Unknown", "Unknown"
    file_id = str(uuid.uuid4())[:8]
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are allowed")
    upload_dir = Path("data/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{file_id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from src.pdf_processor import PDFProcessor
    processor = PDFProcessor()
    content = processor.extract_text_from_pdf(str(file_path))
    combined_text = "".join(content[i]['text'] + "\n" for i in range(min(5, len(content))) if content[i].get('text'))

    if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
        city_name, fiscal_year = await extract_metadata_with_ai(combined_text, config.OPENAI_API_KEY, config.METADATA_EXTRACTION_MODEL)
    if city_name == "Unknown" or fiscal_year == "Unknown":
        regex_city, regex_fy = extract_metadata_from_content(combined_text)
        if city_name == "Unknown" and regex_city != "Unknown":
            city_name = regex_city
        if fiscal_year == "Unknown" and regex_fy != "Unknown":
            fiscal_year = regex_fy
    if city_name == "Unknown" or fiscal_year == "Unknown":
        filename_clean = file.filename.replace('_', ' ').replace('-', ' ')
        if city_name == "Unknown":
            for city in ["pittsburgh", "cleveland", "tulsa", "anaheim", "chicago", "boston", "seattle", "phoenix", "dallas", "houston", "atlanta"]:
                if city in filename_clean.lower():
                    city_name = city.title()
                    break
        if fiscal_year == "Unknown":
            year_match = re.search(r'(\d{4})', filename_clean)
            if year_match:
                fiscal_year = year_match.group(1)

    # Create a safe document ID
    doc_id = f"{clean_city_name(city_name)}_{fiscal_year}".lower()
    logger.info(f"Created document ID: {doc_id} for city: {city_name}, fiscal_year: {fiscal_year}")

    metadata = {
        "file_name": file.filename,
        "city_name": city_name,  # Original city name for display
        "fiscal_year": fiscal_year,
        "file_id": file_id,
        "document_id": doc_id  # Add document_id to metadata
    }
    
    result = rag_system.ingest_document(str(file_path), metadata)

    current_document = {
        "city": city_name,
        "fiscalYear": fiscal_year,
        "fileName": f"{city_name}_Budget_FY{fiscal_year}.pdf",
        "originalFileName": file.filename,
        "fileId": file_id,
        "uploadTime": datetime.utcnow().isoformat(),
        "documentId": doc_id  # Store document_id in current_document
    }
    
    logger.info(f"Document ingested successfully. ID: {doc_id}, City: {city_name}, FY: {fiscal_year}")

    return IngestResponse(
        status=result.get("status", "success"),
        file_id=file_id,
        file_name=file.filename,
        chunks_processed=result.get("chunks_processed", 0),
        pages_processed=result.get("pages_processed", 0),
        city_name=city_name,
        fiscal_year=fiscal_year,
        document_id=doc_id
    )

@app.post("/query", response_model=QueryResponse)
async def query_documents(query: Query):
    try:
        # Always require a document_id for isolation
        doc_id = current_document["documentId"] if current_document else None
        if not doc_id:
            logger.error("No active document found for query")
            raise HTTPException(400, "No document is currently active. Please upload a document first.")
            
        logger.info(f"Query request received. Document ID: {doc_id}, Query: '{query.question}'")
        
        # Use document_id parameter
        result = rag_system.query(query.question, document_id=doc_id, use_cache=query.use_cache)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(500, f"Query error: {str(e)}")

@app.post("/api/clear")
async def clear_document():
    global current_document
    logger.info("Clearing current document")
    current_document = None
    try:
        rag_system.vector_store.reset_active_document_id()
    except Exception as e:
        logger.error(f"Error resetting active document: {e}")
    return {"status": "cleared"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)