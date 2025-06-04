import streamlit as st
import re
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from datetime import datetime

# --- SET PAGE CONFIG AT VERY TOP ---
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

# --- Connect to Google Sheets ---
def connect_to_sheets(sheet_name):
    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        # Prepare credentials dictionary for Streamlit secrets
        credentials_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }

        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )
    except:
        # Fallback to local JSON file (for local development)
        SERVICE_ACCOUNT_FILE = "service_account.json"
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

    client = gspread.authorize(credentials)
    sheet = client.open(sheet_name).sheet1
    return sheet

# --- Log interaction ---
def log_interaction(sheet, user_email, question, answer, feedback):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([user_email, question, answer, feedback, timestamp])

# --- Login Screen ---
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

# ✅ If logged in, proceed with app!

# Connect to Google Sheet
SHEET_NAME = "PHC HR Chatbot Analytics"  # <-- your real Sheet Name
sheet = connect_to_sheets(SHEET_NAME)

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

    # Save last interaction
    st.session_state.last_question = user_input
    st.session_state.last_answer = main_answer.strip()

# ---- Feedback Buttons ----
if st.session_state.get("last_answer"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Yes, it helped", key="feedback_yes"):
            st.success("✅ Thank you for your feedback!")
            log_interaction(
                sheet,
                st.session_state.user_email,
                st.session_state.last_question,
                st.session_state.last_answer,
                "Yes"
            )
            st.session_state.last_answer = None  # Reset

    with col2:
        if st.button("👎 No, it didn't help", key="feedback_no"):
            st.warning("❌ Sorry I'm unable to answer your question. Please contact hr@mespai.com for further assistance.")
            log_interaction(
                sheet,
                st.session_state.user_email,
                st.session_state.last_question,
                st.session_state.last_answer,
                "No"
            )
            st.session_state.last_answer = None  # Reset
