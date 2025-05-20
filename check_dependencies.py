#!/usr/bin/env python3
import sys

def check_import(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False

print("Checking required dependencies...\n")

dependencies = [
    ("PyMuPDF", "fitz"),
    ("pdf2image", "pdf2image"),
    ("pytesseract", "pytesseract"),
    ("camelot", "camelot"),
    ("spacy", "spacy"),
    ("langchain", "langchain"),
    ("tiktoken", "tiktoken"),
    ("openai", "openai"),
    ("pinecone", "pinecone"),  # Changed from pinecone-client
    ("chromadb", "chromadb"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("redis", "redis"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
]

missing = []
for package, module in dependencies:
    if module is None:
        module = package
    if not check_import(module, package):
        missing.append(package)

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    print("\nInstall with:")
    print(f"pip install {' '.join(missing)}")
else:
    print("\nAll dependencies are installed!")

# Check system dependencies
print("\nChecking system dependencies...")
import shutil

if shutil.which("tesseract"):
    print("✓ Tesseract is installed")
else:
    print("✗ Tesseract is NOT installed (needed for OCR)")
    print("  Install with: brew install tesseract")

if shutil.which("pdfinfo") or shutil.which("pdftoppm"):
    print("✓ Poppler is installed")
else:
    print("✗ Poppler is NOT installed (needed for pdf2image)")
    print("  Install with: brew install poppler")