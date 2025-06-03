import re
from PyPDF2 import PdfReader
from tqdm import tqdm
import tiktoken
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Azure config
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_EMBEDDING_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Clients
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name="docs",
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

embedding_client = AzureOpenAI(
    api_key=AZURE_OPENAI_EMBEDDING_API_KEY,
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
    api_version="2024-02-15-preview",
)

# Chunking utility
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

# Section detection regex
SECTION_REGEX = r'^(\d+)\.\s(.+)$'  # e.g., 1. Policy Overview

def parse_sections(raw_text):
    sections = []
    current_section = {"number": None, "title": None, "content": ""}

    for line in raw_text.split("\n"):
        match = re.match(SECTION_REGEX, line.strip())
        if match:
            # Save previous section if exists
            if current_section["number"]:
                sections.append(current_section)
            # Start new section
            current_section = {
                "number": match.group(1),
                "title": match.group(2).strip(),
                "content": ""
            }
        else:
            current_section["content"] += line + " "

    # Add last section
    if current_section["number"]:
        sections.append(current_section)

    return sections

# Read and parse
reader = PdfReader("sample.pdf")
raw_text = ""
for page in reader.pages:
    raw_text += page.extract_text()

sections = parse_sections(raw_text)

# --- Upload with Section Metadata ---
for section in tqdm(sections):
    chunks = chunk_text(section["content"])

    for i, chunk in enumerate(chunks):
        response = embedding_client.embeddings.create(
            input=[chunk],
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )
        embedding = response.data[0].embedding

        record = {
            "id": f"doc-{section['number']}-{i}",
            "content": chunk,
            "section_number": section["number"],
            "section_title": section["title"],
            "document_name": "Mespai Vacation Policy",  # Static for now
            "document_url": "https://docs.google.com/document/d/10QbVhiwQ6Kq70IPcr8wqx8hd15JEbx9m/edit?usp=drive_link&ouid=113900478632323279041&rtpof=true&sd=true",  # Replace with real SharePoint URL
            "embedding": embedding
        }
        search_client.upload_documents(documents=[record])

print("✅ Done embedding and uploading with section metadata!")