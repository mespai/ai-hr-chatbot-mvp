import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import requests

# Load environment variables
load_dotenv(override=True)

# Azure Search Config
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

# Embedding Config
AZURE_OPENAI_EMBEDDING_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Chat Config
AZURE_OPENAI_CHAT_API_KEY = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
AZURE_OPENAI_CHAT_ENDPOINT = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
print(f"DEBUG - AZURE_OPENAI_CHAT_DEPLOYMENT: {AZURE_OPENAI_CHAT_DEPLOYMENT}")

# Clients
embedding_client = AzureOpenAI(
    api_key=AZURE_OPENAI_EMBEDDING_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
)

chat_client = AzureOpenAI(
    api_key=AZURE_OPENAI_CHAT_API_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_CHAT_ENDPOINT
)

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name="docs",
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

def ask_question(query):
    # Step 1: Embed the query
    query_embedding = embedding_client.embeddings.create(
        input=[query],
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    ).data[0].embedding

    # Step 2: Call Azure Search REST API for vector search
    search_url = f"{AZURE_SEARCH_ENDPOINT}/indexes/docs/docs/search?api-version=2023-07-01-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY
    }
    body = {
        "vectors": [{
            "value": query_embedding,
            "fields": "embedding",
            "k": 3
        }],
        "top": 3
    }

    response = requests.post(search_url, headers=headers, json=body)
    response.raise_for_status()
    results = response.json()["value"]

    # --- Format sources properly ---
    sources = []
    for result in results:
        doc_name = result.get("document_name", "Unknown Document")
        section_number = result.get("section_number", "N/A")
        section_title = result.get("section_title", "Untitled Section")
        document_url = result.get("document_url", "")

        if document_url:
            citation = f"{doc_name} — Section {section_number}: {section_title} ([Link to Document]({document_url}))"
        else:
            citation = f"{doc_name} — Section {section_number}: {section_title}"

        sources.append(citation)

    formatted_sources = "\n".join(f"- {src}" for src in sources)

    # Step 3: Build context
    context = ""
    for result in results:
        context += result["content"] + "\n---\n"

    # Step 4: Ask GPT-4 with context
    system_prompt = "You are a helpful HR assistant. Use the context below to answer accurately. If unsure, say so."
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{query}"

    chat_response = chat_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    answer = chat_response.choices[0].message.content.strip()

    # Step 5: Append formatted citations
    return f"{answer}\n\n📚 **Sources:**\n{formatted_sources}"

# --- Test ---
if __name__ == "__main__":
    while True:
        question = input("\nAsk your HR question: ")
        if question.lower() in ["exit", "quit"]:
            break
        answer = ask_question(question)
        print(f"\n🔍 Answer:\n{answer}")