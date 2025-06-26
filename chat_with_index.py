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
AZURE_OPENAI_CHAT_API_VERSION = os.getenv("AZURE_OPENAI_CHAT_API_VERSION")

# Clients
embedding_client = AzureOpenAI(
    api_key=AZURE_OPENAI_EMBEDDING_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
)

chat_client = AzureOpenAI(
    api_key=AZURE_OPENAI_CHAT_API_KEY,
    api_version=AZURE_OPENAI_CHAT_API_VERSION,
    azure_endpoint=AZURE_OPENAI_CHAT_ENDPOINT
)

search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name="docs",
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

# Add at the top, after imports
SYNONYM_MAP = {
    "call in sick": ["report an absence", "illness", "sick day", "miss a shift"],
    "sick": ["illness", "absence", "sick day"],
    "miss a shift": ["absence", "call in sick", "illness"],
    "late": ["tardy", "delayed", "not on time"],
    # Add more as needed
}

def expand_query(query):
    expanded = query
    for phrase, synonyms in SYNONYM_MAP.items():
        if phrase in query.lower():
            expanded += " (" + ", ".join(synonyms) + ")"
    return expanded

def ask_question(query):
    # Expand the query with synonyms before embedding
    query = expand_query(query)
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
            "k": 6  # get more results to allow for both docs
        }],
        "top": 6
    }

    response = requests.post(search_url, headers=headers, json=body)
    response.raise_for_status()
    results = response.json()["value"]

    # --- Group results by document type ---
    grouped = {}
    for result in results:
        doc_name = result.get("document_name", "Unknown Document")
        grouped.setdefault(doc_name, []).append(result)

    # --- Determine which docs are present in top results ---
    contract_doc = "Nurses Bargaining Association 2022-2025 Collective Agreement"
    non_contract_doc = "Terms and Conditions of Employment for Non-Contract Employees"
    present_contract = contract_doc in grouped
    present_non_contract = non_contract_doc in grouped

    # --- Prepare answer blocks ---
    answer_blocks = []
    if present_contract and present_non_contract:
        # Show both contract and non-contract answers
        doc_order = [non_contract_doc, contract_doc]
        for doc_name in doc_order:
            doc_results = grouped[doc_name]
            context = "\n---\n".join(r["content"] for r in doc_results)
            heading = ("For Non-Contract Employees:" if doc_name == non_contract_doc else "For Contract (Nurse) Employees:")
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
            sources = []
            seen = set()
            for result in doc_results:
                section_number = result.get("section_number", "N/A")
                section_title = result.get("section_title", "Untitled Section")
                document_url = result.get("document_url", "")
                key = (doc_name, section_number, section_title, document_url)
                if key in seen:
                    continue
                seen.add(key)
                if document_url:
                    citation = f"{doc_name} — Section {section_number}: {section_title} ([Link to Document]({document_url}))"
                else:
                    citation = f"{doc_name} — Section {section_number}: {section_title}"
                sources.append(citation)
            formatted_sources = "\n".join(f"- {src}" for src in sources)
            answer_blocks.append(f"### {heading}\n{answer}\n\n📚 **Sources:**\n{formatted_sources}")
    else:
        # Show only the single best/highest-confidence answer
        if results:
            best_result = results[0]
            doc_name = best_result.get("document_name", "Unknown Document")
            context = best_result["content"]
            heading = f"For {doc_name}:"
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
            section_number = best_result.get("section_number", "N/A")
            section_title = best_result.get("section_title", "Untitled Section")
            document_url = best_result.get("document_url", "")
            if document_url:
                citation = f"{doc_name} — Section {section_number}: {section_title} ([Link to Document]({document_url}))"
            else:
                citation = f"{doc_name} — Section {section_number}: {section_title}"
            answer_blocks.append(f"### {heading}\n{answer}\n\n📚 **Sources:**\n- {citation}")
    return "\n\n".join(answer_blocks)

# --- Test ---
if __name__ == "__main__":
    while True:
        question = input("\nAsk your HR question: ")
        if question.lower() in ["exit", "quit"]:
            break
        answer = ask_question(question)
        print(f"\n🔍 Answer:\n{answer}")