import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables or secrets
try:
    # Try loading from Streamlit Cloud secrets
    AZURE_OPENAI_CHAT_ENDPOINT = st.secrets["AZURE_OPENAI_CHAT_ENDPOINT"]
    AZURE_OPENAI_CHAT_API_KEY = st.secrets["AZURE_OPENAI_CHAT_API_KEY"]
    AZURE_OPENAI_CHAT_DEPLOYMENT = st.secrets["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    AZURE_OPENAI_EMBEDDING_API_KEY = st.secrets["AZURE_OPENAI_EMBEDDING_API_KEY"]
    AZURE_OPENAI_EMBEDDING_ENDPOINT = st.secrets["AZURE_OPENAI_EMBEDDING_ENDPOINT"]
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = st.secrets["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    AZURE_SEARCH_ENDPOINT = st.secrets["AZURE_SEARCH_ENDPOINT"]
    AZURE_SEARCH_API_KEY = st.secrets["AZURE_SEARCH_API_KEY"]

except Exception:
    # If st.secrets doesn't work, load from .env file
    load_dotenv(override=True)

    AZURE_OPENAI_CHAT_ENDPOINT = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT")
    AZURE_OPENAI_CHAT_API_KEY = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
    AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    AZURE_OPENAI_EMBEDDING_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
    AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

# Import after environment is loaded
from chat_with_index import ask_question

# --- Streamlit UI Config ---
st.set_page_config(page_title="HR Chatbot", page_icon="💬")

st.title("💬 HR Chatbot")
st.caption("Ask me anything about HR policies!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input box
user_input = st.chat_input("Ask your HR question here...")

if user_input:
    # Display user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get answer from backend
    with st.spinner("Thinking..."):
        answer = ask_question(user_input)

    # Split answer and sources
    if "📚 **Sources:**" in answer:
        main_answer, sources = answer.split("📚 **Sources:**", 1)
    else:
        main_answer, sources = answer, ""

    # Display assistant's main answer
    st.chat_message("assistant").markdown(main_answer.strip())
    st.session_state.messages.append({"role": "assistant", "content": main_answer.strip()})

    # Display sources if available
    if sources.strip():
        st.markdown(f"📚 **Sources:**\n{sources.strip()}", unsafe_allow_html=True)