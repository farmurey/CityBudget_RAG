import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Upload a document
files = {'file': open('data/pdfs/SF_Budget_2024.pdf', 'rb')}
data = {
    'city_name': 'San Francisco',
    'fiscal_year': '2024'
}

response = requests.post(f"{BASE_URL}/ingest", files=files, data=data)
print(response.json())

# 2. Query the system
query_data = {
    "question": "What is the transportation budget for San Francisco in 2024?",
    "use_cache": True
}

response = requests.post(f"{BASE_URL}/query", json=query_data)
result = response.json()
print("Answer:", result["answer"])
print("Sources:", result["sources"])