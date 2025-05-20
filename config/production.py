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
    
    # Performance settings
    CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 300
    
    # Security
    API_KEY = os.environ.get('API_KEY')  # For API authentication