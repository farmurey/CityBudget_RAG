from typing import List, Dict, Any
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    def __init__(self):
        self._active_document_id = None

    def set_active_document_id(self, doc_id: str):
        if not doc_id:
            raise ValueError("Document ID cannot be None or empty")
        logger.info(f"Setting active document ID: {doc_id}")
        self._active_document_id = doc_id

    def get_active_document_id(self) -> str:
        if not self._active_document_id:
            logger.error("No active document ID set")
            raise ValueError("No active document set. Please ingest a document first.")
        return self._active_document_id

    def reset_active_document_id(self):
        logger.info("Resetting active document ID")
        self._active_document_id = None

    @abstractmethod
    def store_embeddings(self, chunks: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def query(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        pass


class PineconeVectorStore(VectorStore):
    def __init__(self, api_key: str, environment: str, index_name: str):
        super().__init__()
        from pinecone import Pinecone, ServerlessSpec
        self.pc = Pinecone(api_key=api_key)
        if index_name not in [index.name for index in self.pc.list_indexes()]:
            logger.info(f"Creating new Pinecone index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=environment)
            )
        self.index = self.pc.Index(index_name)
        logger.info(f"Initialized Pinecone vector store with index: {index_name}")

    def store_embeddings(self, chunks: List[Dict[str, Any]]) -> None:
        vectors = []
        document_id = self.get_active_document_id()
        logger.info(f"Storing embeddings for document_id: {document_id}")

        for chunk in chunks:
            if "embedding" in chunk:
                metadata = {**chunk["metadata"], "content": chunk["text"]}
                # Set both document_id and city_name (for backwards compatibility)
                metadata["document_id"] = document_id
                metadata["city_name"] = document_id
                vectors.append({
                    "id": chunk["chunk_id"],
                    "values": chunk["embedding"],
                    "metadata": metadata
                })
                
        logger.info(f"Prepared {len(vectors)} vectors for storage")
        
        # Store in batches
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i + 100]
            logger.info(f"Storing batch of {len(batch)} vectors")
            self.index.upsert(batch)
            
        logger.info(f"Successfully stored {len(vectors)} vectors for document_id: {document_id}")

    def query(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        document_id = self.get_active_document_id()
        logger.info(f"Querying Pinecone for document_id: {document_id}")
        
        # Use both document_id and city_name in filter for robustness
        filter_condition = {
            "$or": [
                {"document_id": {"$eq": document_id}},
                {"city_name": {"$eq": document_id}}
            ]
        }
        
        logger.info(f"Query filter: {filter_condition}")
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_condition
        )
        
        logger.info(f"Retrieved {len(results.matches)} matches from Pinecone")
        
        # Log the document_id of each result for debugging
        for i, match in enumerate(results.matches):
            result_doc_id = match.metadata.get('document_id', 'Unknown')
            result_city_name = match.metadata.get('city_name', 'Unknown')
            logger.info(f"Result {i}: score={match.score}, document_id={result_doc_id}, city_name={result_city_name}")
        
        return [{
            "content": match.metadata.pop("content", ""),
            "metadata": match.metadata,
            "score": match.score
        } for match in results.matches]


class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str = "city_budgets"):
        super().__init__()
        import chromadb
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB vector store with collection: {collection_name}")

    def store_embeddings(self, chunks: List[Dict[str, Any]]) -> None:
        document_id = self.get_active_document_id()
        logger.info(f"Storing embeddings in ChromaDB for document_id: {document_id}")
        ids, embeddings, metadatas, documents = [], [], [], []

        for chunk in chunks:
            if "embedding" in chunk:
                metadata = chunk["metadata"]
                # Set both document_id and city_name (for backwards compatibility)
                metadata["document_id"] = document_id
                metadata["city_name"] = document_id
                ids.append(chunk["chunk_id"])
                embeddings.append(chunk["embedding"])
                metadatas.append(metadata)
                documents.append(chunk["text"])

        logger.info(f"Adding {len(ids)} chunks to ChromaDB")
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info(f"Successfully stored {len(ids)} vectors for document_id: {document_id}")

    def query(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        document_id = self.get_active_document_id()
        logger.info(f"Querying ChromaDB for document_id: {document_id}")
        
        # Use document_id for querying (city_name is also set to document_id for compatibility)
        where_filter = {"$or": [
            {"document_id": document_id},
            {"city_name": document_id}
        ]}
        
        logger.info(f"Query filter: {where_filter}")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        logger.info(f"Retrieved {len(results['ids'][0])} matches from ChromaDB")
        
        # Log the document_id of each result for debugging
        for i in range(len(results['ids'][0])):
            result_doc_id = results['metadatas'][0][i].get('document_id', 'Unknown')
            result_city_name = results['metadatas'][0][i].get('city_name', 'Unknown')
            logger.info(f"Result {i}: distance={results['distances'][0][i]}, document_id={result_doc_id}, city_name={result_city_name}")
        
        return [{
            "content": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "score": 1 - results['distances'][0][i]  # Convert distance to similarity score
        } for i in range(len(results['ids'][0]))]