from fastapi import FastAPI, Depends, HTTPException, Header
from api import app as base_app
import os

# Add authentication middleware
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.environ.get('API_KEY'):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# Add authentication to all endpoints
for route in base_app.routes:
    if route.path != "/health":
        route.dependencies.append(Depends(verify_api_key))

app = base_app