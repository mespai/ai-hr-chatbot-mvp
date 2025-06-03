import streamlit as st
import re
import os
from dotenv import load_dotenv

st.set_page_config(page_title="HR Chatbot", page_icon="💬", layout="wide")

# --- Allowed Domains List ---
ALLOWED_DOMAINS = ["mespai.com", "providencehealth.bc.ca", "gmail.com"]

# --- Validate email domain ---
def is_valid_domain(email):
    try:
        domain = email.split('@')[1]
        return domain.lower() in ALLOWED_DOMAINS
    except:
        return False

# --- Login ---
if "user_email" not in st.session_state:
    st.title("🔒 Secure Access")
    st.caption("Please enter your work email to continue.")

    email_input = st.text_input("Work Email", placeholder="you@mespai.com")

    if st.button("Continue"):
        if is_valid_domain(email_input):
            st.session_state.user_email = email_input.lower()
            st.success(f"✅ Welcome, {email_input.split('@')[0]}!")
            st.rerun()
        else:
            st.error("❌ Unauthorized domain. Please use a valid company email.")
    st.stop()

# Load environment
try:
    AZURE_OPENAI_CHAT_ENDPOINT = st.secrets["AZURE_OPENAI_CHAT_ENDPOINT"]
    AZURE_OPENAI_CHAT_API_KEY = st.secrets["AZURE_OPENAI_CHAT_API_KEY"]
    AZURE_OPENAI_CHAT_DEPLOYMENT = st.secrets["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    AZURE_OPENAI_EMBEDDING_API_KEY = st.secrets["AZURE_OPENAI_EMBEDDING_API_KEY"]
    AZURE_OPENAI_EMBEDDING_ENDPOINT = st.secrets["AZURE_OPENAI_EMBEDDING_ENDPOINT"]
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = st.secrets["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    AZURE_SEARCH_ENDPOINT = st.secrets["AZURE_SEARCH_ENDPOINT"]
    AZURE_SEARCH_API_KEY = st.secrets["AZURE_SEARCH_API_KEY"]

except Exception:
    load_dotenv(override=True)
    AZURE_OPENAI_CHAT_ENDPOINT = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT")
    AZURE_OPENAI_CHAT_API_KEY = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
    AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    AZURE_OPENAI_EMBEDDING_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
    AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

# Import backend logic
from chat_with_index import ask_question

# --- Streamlit UI Chatbot ---
st.title("💬 HR Chatbot")
st.caption(f"Welcome, {st.session_state.user_email}!")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Ask your HR question here...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        answer = ask_question(user_input)

    # Save last answer for feedback buttons
    st.session_state.last_answer = answer

    st.chat_message("assistant").markdown(answer.strip())
    st.session_state.messages.append({"role": "assistant", "content": answer.strip()})

# --- Feedback Buttons ---
if st.session_state.get("last_answer"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Yes, it helped", key="feedback_yes"):
            st.success("✅ Thank you for your feedback!")
            st.session_state.last_answer = None  # Reset
    with col2:
        if st.button("👎 No, it didn't help", key="feedback_no"):
            st.warning("❌ Sorry I'm unable to answer your question. Please contact hr@mespai.com for further assistance.")
            st.session_state.last_answer = None  # Reset