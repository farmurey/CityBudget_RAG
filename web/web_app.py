# web_app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI backend
UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

# Ensure folders exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(STATIC_FOLDER).mkdir(exist_ok=True)

# Store uploaded documents info (in production, use a database)
uploaded_documents = []

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if the backend API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return jsonify({"status": "healthy", "backend": response.json()})
    except:
        return jsonify({"status": "unhealthy", "backend": None}), 503

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    return jsonify(uploaded_documents)

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Proxy upload to the FastAPI backend"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    city_name = request.form.get('city_name', '')
    fiscal_year = request.form.get('fiscal_year', '')
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Forward to FastAPI backend
    files = {'file': (file.filename, file.stream, file.content_type)}
    data = {
        'city_name': city_name,
        'fiscal_year': fiscal_year
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/ingest", files=files, data=data)
        
        if response.ok:
            result = response.json()
            # Store document info
            uploaded_documents.append({
                'city': city_name,
                'fiscalYear': fiscal_year,
                'fileName': file.filename,
                'fileId': result.get('file_id', ''),
                'chunksProcessed': result.get('chunks_processed', 0),
                'pagesProcessed': result.get('pages_processed', 0)
            })
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to process document"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_documents():
    """Proxy query to the FastAPI backend"""
    data = request.json
    
    try:
        response = requests.post(f"{API_BASE_URL}/query", json=data)
        
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to get response"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of cities with uploaded documents"""
    cities = list(set(doc['city'] for doc in uploaded_documents))
    return jsonify(cities)

# Serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(STATIC_FOLDER, path)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    Path('templates').mkdir(exist_ok=True)
    
    # Save the HTML to templates/index.html
    # In production, you'd have this as a separate file
    
    app.run(debug=True, port=5000)
                