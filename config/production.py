import os
from src.config import Config

class ProductionConfig(Config):
    # Override defaults for production
    DEBUG = False
    
    # Use environment variables
    OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
    PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
    PINECONE_ENV = os.environ['PINECONE_ENV']
    
    # Redis cluster
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis-cluster')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    
    # Model settings
    LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o-mini')
    METADATA_EXTRACTION_MODEL = os.environ.get('METADATA_EXTRACTION_MODEL', 'gpt-4o-mini')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Performance settings
    CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 300
    
    # Security
    API_KEY = os.environ.get('API_KEY')  # For API authentication