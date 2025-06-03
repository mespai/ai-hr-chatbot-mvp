from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile
)
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv
from azure.search.documents.indexes.models import (
    SearchIndex, 
    SimpleField, 
    SearchableField, 
    SearchField,  # Add this line
    SearchFieldDataType, 
    VectorSearch, 
    HnswAlgorithmConfiguration, 
    VectorSearchProfile
)

load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

index_client = SearchIndexClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)

index_name = "docs"  # Must match your actual index name

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="section_number", type=SearchFieldDataType.String),
    SearchableField(name="section_title", type=SearchFieldDataType.String),
    SimpleField(name="document_name", type=SearchFieldDataType.String),
    SimpleField(name="document_url", type=SearchFieldDataType.String),
SearchField(
    name="embedding",
    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
    searchable=True,
    vector_search_dimensions=1536,
    vector_search_profile_name="my-vector-config"  # Add '_name' suffix
)
]

vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")],
    profiles=[VectorSearchProfile(name="my-vector-config", algorithm_configuration_name="my-hnsw")]
)

index = SearchIndex(
    name=index_name,
    fields=fields,
    vector_search=vector_search
)

# Delete and recreate (careful! deletes old data)
try:
    index_client.delete_index(index_name)
except:
    pass  # ignore if index doesn't exist yet

index_client.create_index(index)

print(f"✅ Index '{index_name}' created with new schema!")