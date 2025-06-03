import os
import openai
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType
)
from azure.search.documents.indexes.models import (
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile
)
from azure.search.documents.indexes.models._index import SearchField
from azure.identity import DefaultAzureCredential
from PyPDF2 import PdfReader
from tqdm import tqdm
import tiktoken

# Load .env
load_dotenv()

# ENV variables
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Clients
search_credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name="docs",
    credential=search_credential
)
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
# --- STEP 1: Read + Chunk the PDF ---
def chunk_text(text, max_tokens=500):
    encoding = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks = []
    current = []
    current_tokens = 0

    for word in words:
        tokens = len(encoding.encode(word))
        if current_tokens + tokens > max_tokens:
            chunks.append(" ".join(current))
            current = [word]
            current_tokens = tokens
        else:
            current.append(word)
            current_tokens += tokens

    if current:
        chunks.append(" ".join(current))

    return chunks

reader = PdfReader("sample.pdf")
raw_text = ""
for page in reader.pages:
    raw_text += page.extract_text()

chunks = chunk_text(raw_text)

# --- STEP 2: Embed and Upload ---
for i, chunk in enumerate(tqdm(chunks)):
    response = openai.embeddings.create(
        input=[chunk],
        model=AZURE_OPENAI_DEPLOYMENT
    )
    embedding = response.data[0].embedding

    record = {
        "id": f"doc-{i}",
        "content": chunk,
        "embedding": embedding
    }
    search_client.upload_documents(documents=[record])

print("✅ Done embedding and uploading to Azure AI Search")
