import streamlit as st
import re
import os
from dotenv import load_dotenv

# --- SET PAGE CONFIG AT VERY TOP ---
st.set_page_config(page_title="HR Chatbot", page_icon="💬", layout="wide")

# --- Allowed Domains List ---
ALLOWED_DOMAINS = ["mespai.com", "providencehealth.bc.ca", "gmail.com"]

# --- Function to validate email domain ---
def is_valid_domain(email):
    try:
        domain = email.split('@')[1]
        return domain.lower() in ALLOWED_DOMAINS
    except:
        return False

# --- Login Screen Logic ---
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
    st.stop()  # Prevent rest of app from loading if not logged in

# ✅ If logged in, proceed with app!

# Load environment variables or secrets
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

# Import after environment is loaded
from chat_with_index import ask_question

# --- Streamlit UI Chatbot ---
st.title("💬 HR Chatbot")
st.caption(f"Welcome, {st.session_state.user_email}!")

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

    # --- NEW: Add Feedback Buttons (after displaying the bot response) ---
    st.write("Was this answer helpful?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Yes", key=f"yes_{len(st.session_state.messages)}"):
            st.success("✅ Thanks for the feedback!")
    with col2:
        if st.button("👎 No", key=f"no_{len(st.session_state.messages)}"):
            st.error("❌ Sorry I'm unable to answer your question, please contact hr@mespai.com for further assistance.")