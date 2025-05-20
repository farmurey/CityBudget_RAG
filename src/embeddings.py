from openai import OpenAI
import numpy as np
from typing import List, Dict, Any
from tqdm import tqdm
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            raise ValueError("OpenAI API key must be provided or set in environment variables")
        
        # For newer versions of OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except TypeError:
            # Fallback for older versions
            import openai
            openai.api_key = api_key
            self.client = openai
            
        self.model = model
        
    def generate_embeddings(self, chunks: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Generate embeddings for text chunks"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        for i in tqdm(range(0, len(chunks), batch_size), desc="Generating embeddings"):
            batch = chunks[i:i + batch_size]
            texts = [chunk["text"] for chunk in batch]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                for j, embedding in enumerate(response.data):
                    chunks[i + j]["embedding"] = embedding.embedding
                    
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                raise
        
        return chunks
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise