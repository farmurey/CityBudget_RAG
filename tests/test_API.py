from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="City Budget RAG API - Test")

class Query(BaseModel):
    question: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/test-query")
async def test_query(query: Query):
    return {"answer": f"Test response for: {query.question}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)