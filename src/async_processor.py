from celery import Celery
import json
from src.config import Config
from main import CityBudgetRAG

# Initialize Celery
celery_app = Celery(
    'city_budget_rag',
    broker=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/1',
    backend=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/2'
)

@celery_app.task(bind=True)
def process_document_async(self, pdf_path: str, metadata: dict):
    """Async document processing task"""
    try:
        config = Config()
        rag = CityBudgetRAG(config)
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Extracting text...'})
        
        result = rag.ingest_document(pdf_path, metadata)
        
        return {
            'status': 'SUCCESS',
            'result': result
        }
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }