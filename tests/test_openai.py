from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="test"
)
print("Embedding generated successfully!")