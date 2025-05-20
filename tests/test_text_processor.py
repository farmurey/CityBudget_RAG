import unittest
from src.text_processor import TextProcessor

class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()
    
    def test_clean_text(self):
        text = "Page 1  of  10\n\n\n\nBudget   Summary"
        cleaned = self.processor.clean_text(text)
        self.assertEqual(cleaned, "Budget Summary")
    
    def test_chunk_text(self):
        text = "This is a test. " * 100
        chunks = self.processor.chunk_text(text)
        self.assertTrue(len(chunks) > 0)
        self.assertTrue(all(len(chunk) <= 1000 for chunk in chunks))

if __name__ == '__main__':
    unittest.main()