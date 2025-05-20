# main.py
import logging
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from src.config import Config
from src.pdf_processor import PDFProcessor
from src.text_processor import TextProcessor
from src.embeddings import EmbeddingGenerator
from src.vector_store import PineconeVectorStore, ChromaVectorStore
from src.query_engine import QueryEngine

# Set up logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_city_name(city_name: str) -> str:
    return city_name.lower().replace("city of", "").replace("municipality of", "").strip().replace(" ", "_")

def safe_document_id(city_name: str, fiscal_year: str) -> str:
    city_clean = clean_city_name(city_name or "unknown")
    fiscal_year_clean = fiscal_year.strip() if fiscal_year else "unknown"
    return f"{city_clean}_{fiscal_year_clean}".lower()

class CityBudgetRAG:
    def __init__(self, config: Config):
        self.config = config
        
        try:
            self.pdf_processor = PDFProcessor()
            self.text_processor = TextProcessor(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP
            )
            self.embedding_generator = EmbeddingGenerator(
                api_key=config.OPENAI_API_KEY,
                model=config.EMBEDDING_MODEL
            )
            self.vector_store = self._initialize_vector_store(config)
            
            redis_config = {
                "host": config.REDIS_HOST,
                "port": config.REDIS_PORT,
                "db": config.REDIS_DB
            } if config.REDIS_HOST else None
            
            self.query_engine = QueryEngine(
                openai_api_key=config.OPENAI_API_KEY,
                vector_store=self.vector_store,
                embedding_generator=self.embedding_generator,
                redis_config=redis_config
            )
            
            self.vector_store.reset_active_document_id()
            logger.info("CityBudgetRAG initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CityBudgetRAG: {e}")
            raise
    
    def _initialize_vector_store(self, config):
        if config.PINECONE_API_KEY and config.PINECONE_ENV:
            try:
                logger.info("Attempting to initialize Pinecone...")
                return PineconeVectorStore(
                    api_key=config.PINECONE_API_KEY,
                    environment=config.PINECONE_ENV,
                    index_name=config.VECTOR_DB_INDEX
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}")
                logger.info("Falling back to ChromaDB...")
        
        logger.info("Using ChromaDB as vector store")
        return ChromaVectorStore(collection_name=config.VECTOR_DB_INDEX)
    
    def ingest_document(self, pdf_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Ingesting document: {pdf_path}")
        try:
            # Use the document_id from metadata if provided, otherwise create one
            doc_id = metadata.get("document_id") or safe_document_id(
                metadata["city_name"], metadata["fiscal_year"])
            
            logger.info(f"Using document_id for ingestion: {doc_id}")
            self.vector_store.set_active_document_id(doc_id)

            pdf_content = self.pdf_processor.extract_text_from_pdf(pdf_path)
            chunks = self.text_processor.process_document_content(pdf_content, metadata)
            chunks_with_embeddings = self.embedding_generator.generate_embeddings(chunks)

            # Enforce document_id into all chunks metadata for filtering
            for chunk in chunks_with_embeddings:
                chunk["metadata"]["document_id"] = doc_id
                # For backward compatibility, also set city_name as document_id
                chunk["metadata"]["city_name"] = doc_id
                
            logger.info(f"Generated {len(chunks_with_embeddings)} chunks with embeddings")
            self.vector_store.store_embeddings(chunks_with_embeddings)
            logger.info(f"Stored embeddings in vector store with document_id: {doc_id}")

            return {
                "status": "success",
                "file": metadata["file_name"],
                "chunks_processed": len(chunks),
                "pages_processed": len(pdf_content),
                "city_name": metadata["city_name"],
                "fiscal_year": metadata["fiscal_year"],
                "document_id": doc_id
            }

        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def query(self, question: str, document_id: str = None, use_cache: bool = True) -> Dict[str, Any]:
        try:
            if not document_id:
                logger.error("No document_id provided for query")
                raise ValueError("No document_id provided for query. Please upload a document first.")
                
            logger.info(f"Processing query with document_id: {document_id}")
            logger.info(f"Query: '{question}'")
            
            return self.query_engine.answer_query(
                question,
                document_id=document_id,
                use_cache=use_cache
            )
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {
                "answer": "Sorry, an error occurred while processing your query.",
                "sources": [],
                "error": str(e),
                "timestamp": str(datetime.now()),
                "metadata": {}
            }

    def get_active_document_id(self):
        return self.vector_store.get_active_document_id()