import re
from PyPDF2 import PdfReader
from tqdm import tqdm
import tiktoken
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import requests
from io import BytesIO
import uuid

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

# Document list
documents = [
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Common%20Themes%20of%20Questions%20that%20Employees%20.pdf",
        "name": "Common Themes of Questions that Employees Ask"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/PHC%20NEE%20FAQ%202025.pdf",
        "name": "PHC New Employee Onboarding FAQ 2025"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Terms%20and%20Conditions%20of%20Employment%20for%20Non%20Contract%20Employees.pdf",
        "name": "Terms and Conditions of Employment for Non-Contract Employees"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Nurses%20Bargaining%20Association%202022-2025%20Collective%20Agreement.pdf",
        "name": "Nurses Bargaining Association 2022-2025 Collective Agreement"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Andgo%20Login%20Guide.pdf",
        "name": "Andgo Login Guide"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Andgo%20User%20A%20Guide%20-%20How%20to%20Apply%20for%20Shifts%20and%20Blocks.pdf",
        "name": "Andgo User A Guide - How to Apply for Shifts and Blocks"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Andgo%20User%20Guide%20-%20How%20to%20Change%20Your%20Smart%20Call%20Preferences.pdf",
        "name": "Andgo User Guide - How to Change Your Smart Call Preferences"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Andgo%20User%20Guide%20-%20How%20to%20View%20MySchedule.pdf",
        "name": "Andgo User Guide - How to View MySchedule"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/Angdo%20User%20Guide%20-%20How%20to%20View%20My%20Information.pdf",
        "name": "Angdo User Guide - How to View My Information"
    },
    {
        "url": "https://mespaihrchatbotstorage.blob.core.windows.net/phchrchatbotmvpfiles/EARL%20Employee%20Guide.pdf",
        "name": "EARL Employee Guide"
    }
]

# Chunking function
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

# Fetch and parse remote PDF
def fetch_and_parse_pdf(url):
    response = requests.get(url)
    response.raise_for_status()
    pdf_bytes = BytesIO(response.content)
    reader = PdfReader(pdf_bytes)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def parse_faq_sections(text):
    # Split on Q: or Q. or bullet points (\u2022 or -)
    sections = []
    # Try Q: or Q. style
    faq_parts = re.split(r'(?=^Q[:.])', text, flags=re.MULTILINE)
    if len(faq_parts) > 1:
        for part in faq_parts:
            if not part.strip():
                continue
            lines = part.strip().split('\n', 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            sections.append({
                "number": None,
                "title": title,
                "content": content
            })
        return sections
    # Try bullet point style (• or -)
    bullet_parts = re.split(r'(?=^[\u2022\-] )', text, flags=re.MULTILINE)
    if len(bullet_parts) > 1:
        for part in bullet_parts:
            if not part.strip():
                continue
            lines = part.strip().split('\n', 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            sections.append({
                "number": None,
                "title": title,
                "content": content
            })
        return sections
    return []

def parse_lettered_sections(text):
    sections = []
    matches = list(re.finditer(r'^([A-Z])\)\s+(.+)$', text, flags=re.MULTILINE))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append({
            "number": match.group(1),
            "title": match.group(2),
            "content": content
        })
    return sections

def parse_sections(text):
    # Try FAQ style first
    faq_sections = parse_faq_sections(text)
    if len(faq_sections) > 1:
        return faq_sections
    # Try lettered sections
    lettered_sections = parse_lettered_sections(text)
    if len(lettered_sections) > 1:
        return lettered_sections
    # Fallback: treat whole doc as one section
    return [{"number": "1", "title": "Full Document", "content": text}]

# Main embed loop
print("RUNNING:", __file__)
for doc in documents:
    print(f"Fetching and parsing: {doc['url']}")
    content = fetch_and_parse_pdf(doc["url"])
    sections = parse_sections(content)
    safe_name = re.sub(r'[^A-Za-z0-9_\-=]', '_', doc['name'])
    for section in sections:
        section_number = section["number"] if section["number"] else ""
        section_title = section["title"] if section["title"] else ""
        section_chunks = chunk_text(section["content"])
        for j, chunk in enumerate(section_chunks):
            response = embedding_client.embeddings.create(
                input=[chunk],
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            embedding = response.data[0].embedding
            metadata = {
                "id": f"{safe_name}_section_{section_number}_{j+1}_{uuid.uuid4().hex[:8]}",
                "content": chunk,
                "embedding": embedding,
                "document_name": doc["name"],
                "document_url": doc["url"],
                "section_number": section_number,
                "section_title": section_title
            }
            search_client.upload_documents(documents=[metadata])
print("✅ All documents embedded and uploaded to Azure AI Search.")