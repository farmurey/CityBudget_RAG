import re
import spacy
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from typing import List, Dict, Any
import hashlib
from datetime import datetime

nlp = spacy.load("en_core_web_sm")


class TextProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove page numbers, headers, footers
        text = re.sub(r'Page \d+\s*of\s*\d+', '', text)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Normalize numbers and currency
        text = re.sub(r'\$\s*([0-9,]+)', r'$\1', text)
        text = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1,\2', text)
        
        return text.strip()
    
    def process_table(self, table_text: str) -> str:
        """Process and format table text"""
        lines = table_text.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Convert excessive spaces to pipe separators
            cleaned_line = re.sub(r'\s{2,}', ' | ', line.strip())
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=lambda t: len(self.encoding.encode(t)),
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        return chunks
    
    def process_document_content(self, content: List[Dict[str, Any]], 
                               doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process entire document content"""
        all_chunks = []
        
        for page_data in content:
            # Clean text
            cleaned_text = self.clean_text(page_data['text'])
            
            # Process tables
            cleaned_tables = [self.process_table(table) for table in page_data['tables']]
            
            # Combine text and tables
            combined_text = cleaned_text
            if cleaned_tables:
                combined_text += "\n\n" + "\n\n".join(cleaned_tables)
            
            # Create chunks
            chunks = self.chunk_text(combined_text)
            
            # Create metadata for each chunk
            for i, chunk in enumerate(chunks):
                chunk_metadata = self._create_chunk_metadata(
                    chunk, doc_metadata, page_data['page_num'], i
                )
                all_chunks.append(chunk_metadata)
        
        return all_chunks
    
    def _create_chunk_metadata(self, chunk_text: str, doc_metadata: Dict[str, Any],
                             page_num: int, chunk_num: int) -> Dict[str, Any]:
        """Create metadata for a chunk"""
        chunk_id = hashlib.md5(
            f"{doc_metadata['file_name']}_{page_num}_{chunk_num}".encode()
        ).hexdigest()[:12]
        
        return {
            "chunk_id": chunk_id,
            "text": chunk_text,
            "metadata": {
                "city_name": doc_metadata.get("city_name"),
                "fiscal_year": doc_metadata.get("fiscal_year"),
                "document_type": "budget",
                "page_number": page_num,
                "chunk_number": chunk_num,
                "file_name": doc_metadata["file_name"],
                "section": self._extract_section(chunk_text),
                "created_at": datetime.utcnow().isoformat(),
                "char_count": len(chunk_text),
                "token_count": len(self.encoding.encode(chunk_text))
            }
        }
    
    def _extract_section(self, text: str) -> str:
        """Extract section from text (safe version)"""
        # Look for common budget section headers
        patterns = [
            r'(Revenue|Expenses|Capital|Transportation|Education|Public Safety|Health)',    # ✅ has group
            r'Department of ([\w\s]+)',                                                      # ✅ added group
            r'^\s*\d+\.\s*([A-Z][^.]+)'                                                     # ✅ has group
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:200], re.IGNORECASE)
            if match:
                # Check if pattern has capturing groups
                if match.lastindex:   # ✅ safe check
                    return match.group(1).strip()
                else:
                    return match.group(0).strip()  # fallback → full match

        return "General"
