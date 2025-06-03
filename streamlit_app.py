import os
import streamlit as st
from dotenv import load_dotenv

# Load local .env if running locally
load_dotenv(override=True)

# Detect if running in Streamlit Cloud (st.secrets is populated)
if "AZURE_OPENAI_CHAT_ENDPOINT" in st.secrets:
    # Running on Streamlit Cloud
    AZURE_OPENAI_CHAT_ENDPOINT = st.secrets["AZURE_OPENAI_CHAT_ENDPOINT"]
    AZURE_OPENAI_CHAT_API_KEY = st.secrets["AZURE_OPENAI_CHAT_API_KEY"]
    AZURE_OPENAI_CHAT_DEPLOYMENT = st.secrets["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    AZURE_OPENAI_EMBEDDING_API_KEY = st.secrets["AZURE_OPENAI_EMBEDDING_API_KEY"]
    AZURE_OPENAI_EMBEDDING_ENDPOINT = st.secrets["AZURE_OPENAI_EMBEDDING_ENDPOINT"]
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = st.secrets["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    AZURE_SEARCH_ENDPOINT = st.secrets["AZURE_SEARCH_ENDPOINT"]
    AZURE_SEARCH_API_KEY = st.secrets["AZURE_SEARCH_API_KEY"]
else:
    # Running locally
    AZURE_OPENAI_CHAT_ENDPOINT = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT")
    AZURE_OPENAI_CHAT_API_KEY = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
    AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    AZURE_OPENAI_EMBEDDING_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
    AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

import streamlit as st
from chat_with_index import ask_question

st.set_page_config(page_title="HR Chatbot", page_icon="💬")

st.title("💬 HR Chatbot")
st.write("Ask me anything about HR policies!")

# Input
user_input = st.text_input("Your Question")

# When the user submits
if st.button("Ask"):
    if user_input:
        with st.spinner("Thinking..."):
            answer = ask_question(user_input)
        st.success(answer)