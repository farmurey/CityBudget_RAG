from openai import OpenAI
import redis
import json
import hashlib
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self, openai_api_key: str, vector_store, embedding_generator, redis_config: Optional[Dict] = None, llm_model: str = "gpt-4o-mini"):
        self.llm_client = OpenAI(api_key=openai_api_key)
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.redis_client = redis.Redis(**redis_config) if redis_config else None
        self.llm_model = llm_model

    def answer_query(self, query: str, document_id: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate an answer for a query using document-specific context.
        
        Args:
            query: The user's question
            document_id: ID of the document to query against (required)
            use_cache: Whether to use cached results if available
            
        Returns:
            Dict containing the answer and metadata
        """
        if not document_id:
            logger.error("No document_id provided for query")
            raise ValueError("No document_id provided for query")
            
        # Set the active document for the vector store
        logger.info(f"Setting active document_id for query: {document_id}")
        self.vector_store.set_active_document_id(document_id)
        
        # Verify the active document was set correctly
        active_doc = self.vector_store.get_active_document_id()
        logger.info(f"Confirmed active document_id: {active_doc}")
        
        # Check if we have a cached response
        if use_cache and self.redis_client:
            cached = self._check_cache(query, document_id)
            if cached:
                logger.info(f"Cache hit for query with document_id: {document_id}")
                return cached

        # Generate query embedding
        logger.info("Generating query embedding")
        query_embedding = self.embedding_generator.generate_query_embedding(query)
        
        # Retrieve relevant chunks
        logger.info(f"Retrieving relevant chunks for document_id: {document_id}")
        relevant_chunks = self.vector_store.query(query_embedding, top_k=5)
        logger.info(f"Retrieved {len(relevant_chunks)} chunks")
        
        # Log chunk sources for debugging
        for i, chunk in enumerate(relevant_chunks):
            chunk_doc = chunk['metadata'].get('document_id', 'Unknown')
            chunk_city = chunk['metadata'].get('city_name', 'Unknown')
            logger.info(f"Chunk {i}: document_id={chunk_doc}, city_name={chunk_city}")
            
        # Generate answer
        answer = self._generate_answer(query, relevant_chunks)
        response = self._format_response(answer, relevant_chunks)

        # Cache the result if enabled
        if use_cache and self.redis_client:
            self._cache_result(query, response, document_id)
            
        return response

    def _generate_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Generate an answer using the LLM based on retrieved chunks"""
        context = "\n\n".join([
            f"[Source: Page {chunk['metadata']['page_number']}, {chunk['metadata']['file_name']}]\n{chunk['content']}"
            for chunk in chunks
        ])
        if not chunks or len(context.strip()) == 0:
            logger.warning("No relevant chunks found; returning explanatory fallback.")
            return (
        "The budget document does not include a specific section for this topic. "
        "The information may appear in the detailed departmental budget rather than in the Budget in Brief."
    )

        prompt = f"""You are analyzing city budget documents. Answer based ONLY on the provided context.

Context:
{context}

Question: {query}

Instructions:
1. Use only the context provided.
2. Cite page numbers and document names where possible.
3. If the document does not include the specific information requested, explain that it is not detailed in this document and, if relevant, mention where such information might typically appear (for example, in a department-level or detailed budget section).
4. If you find partial information, summarize what is available instead of saying there is not enough information.
5. Be clear, factual, and concise.

Answer:"""
        logger.info(f"Sending query to LLM for answer generation using model: {self.llm_model}")
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "You are a municipal budget analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        logger.info("Received response from LLM")
        return response.choices[0].message.content

    def _format_response(self, answer: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the response with sources and metadata"""
        sources = [{
            "reference": f"[{i+1}]",
            "page": chunk['metadata']['page_number'],
            "document": chunk['metadata']['file_name'],
            "city": chunk['metadata'].get('city_name', 'Unknown'),
            "fiscal_year": chunk['metadata'].get('fiscal_year', 'Unknown'),
            "document_id": chunk['metadata'].get('document_id', 'Unknown'),  # Include document_id
            "score": round(chunk['score'], 3)
        } for i, chunk in enumerate(chunks)]
        return {
            "answer": answer,
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "chunks_retrieved": len(chunks),
                "confidence_scores": [chunk['score'] for chunk in chunks],
                "document_id": chunks[0]['metadata'].get('document_id', 'Unknown') if chunks else 'Unknown'  # Include document_id
            }
        }

    def _check_cache(self, query: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Check if the query result is cached"""
        key = f"query:{document_id}:{hashlib.md5(query.encode()).hexdigest()}"
        try:
            cached = self.redis_client.get(key)
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")
            return None

    def _cache_result(self, query: str, result: Dict[str, Any], document_id: str, ttl: int = 3600) -> None:
        """Cache the query result"""
        key = f"query:{document_id}:{hashlib.md5(query.encode()).hexdigest()}"
        try:
            self.redis_client.setex(key, ttl, json.dumps(result))
            logger.info(f"Cached result for document_id: {document_id}")
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
            pass