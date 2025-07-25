import streamlit as st
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image  # <--- Add this for image handling

load_dotenv()

# --- SET PAGE CONFIG AT VERY TOP ---
st.set_page_config(page_title="HR Chatbot", page_icon="💬", layout="wide")

# Add custom CSS for left alignment at the top after st.set_page_config
st.markdown("""
    <style>
    .element-container .stMarkdown, .element-container .stMarkdown p {
        text-align: left !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    .stChatMessageContent, .stMarkdown {
        text-align: left !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    gcp_service_account = os.getenv("GCP_SERVICE_ACCOUNT")
    if not gcp_service_account:
        # Bypass for local development
        class DummySheet:
            def append_row(self, row):
                pass
        return DummySheet()
    try:
        service_account_info = json.loads(gcp_service_account)
    except Exception:
        # If JSON is invalid, bypass as well
        class DummySheet:
            def append_row(self, row):
                pass
        return DummySheet()
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        service_account_info,
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
# --- Login Screen ---
if "user_email" not in st.session_state:
    # One column, align left
    st.image("phc_logo.png", width=200)  # Make the logo bigger (adjust width as needed)
    st.markdown("<h1 style='text-align: left; margin-top: 0;'>HR Chatbot Login</h1>", unsafe_allow_html=True)
    st.caption("Please enter your work email to continue.")

    email_input = st.text_input("Work Email", placeholder="email@providencehealth.bc.ca")

    if st.button("Continue"):
        if is_valid_domain(email_input):
            st.session_state.user_email = email_input.lower()
            st.success("Welcome!")
            st.rerun()
        else:
            st.error("❌ Unauthorized domain. Please use a valid company email.")

    # Place your welcome message here, before st.stop()
    st.markdown("""
    <div style="
        background-color: #fffbe6;
        border-left: 6px solid #ffe066;
        padding: 1.5em 1.5em 1.5em 1.5em;
        border-radius: 8px;
        margin-top: 1.5em;
        margin-bottom: 1.5em;
    ">
    <b>Welcome to the HR Chatbot (Proof of Concept)</b><br>
    Thank you for participating in this early test of our HR Chatbot. This tool is currently being tested as part of our ongoing efforts to improve how employees access important information.<br>
    <br>
    <b>Please note:</b>
    <ul style=\"margin-top: 0;\">  <!-- This line is changed -->
    <li>This chatbot is for testing purposes only and may not have answers to all questions.</li>
    <li>It is trained on a limited set of HR and onboarding materials, including:
        <ul>
            <li>Common Employee Questions</li>
            <li>PHC Onboarding FAQ 2025</li>
            <li>Terms and Conditions of Employment for Non-Contract Employees</li>
            <li>NBA Collective Agreement (2022–2025)</li>
            <li>Andgo System Guides</li>
            <li>EARL Employee Guide</li>
        </ul>
    </li>
    </ul>
    <b>Disclaimer:</b> This chatbot is not a replacement for official HR guidance. For questions not covered by the sources above, or for any urgent HR-related issues, please contact your HR representative directly.
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ✅ If logged in, proceed with app!

# Connect to Google Sheet
SHEET_NAME = "PHC HR Chatbot Analytics"  # <-- Your Sheet Name
sheet = connect_to_sheets(SHEET_NAME)

# Load environment variables
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

# After successful login (Main Page)

# Load PHC logo
st.image("phc_logo.png", width=200)  # Adjust width as needed

# Title without emoji
st.title("How can I help you today?")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages (only completed ones)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message["content"], unsafe_allow_html=True)
            if message.get("sources"):
                st.markdown(f"📚 **Sources:**\n{message['sources']}", unsafe_allow_html=True)
        else:
            st.markdown(message["content"], unsafe_allow_html=True)

# Chat input box
user_input = st.chat_input("Ask your HR question here...")

if user_input:
    # Show spinner below the chat while waiting for assistant response
    with st.spinner("Thinking..."):
        answer = ask_question(user_input)
        # Split answer and sources
        if "📚 **Sources:**" in answer:
            main_answer, sources = answer.split("📚 **Sources:**", 1)
        else:
            main_answer, sources = answer, ""
        user_message = {"role": "user", "content": user_input}
        assistant_message = {
            "role": "assistant",
            "content": main_answer.strip(),
            "sources": sources.strip() if sources.strip() else None
        }
        st.session_state.messages.append(user_message)
        st.session_state.messages.append(assistant_message)
        # Display the new user message
        with st.chat_message("user"):
            st.markdown(user_input)
        # Display the new assistant message
        with st.chat_message("assistant"):
            st.markdown(assistant_message["content"], unsafe_allow_html=True)
            if assistant_message.get("sources"):
                st.markdown(f"📚 **Sources:**\n{assistant_message['sources']}", unsafe_allow_html=True)
    # Save last interaction
    st.session_state.last_question = user_input
    st.session_state.last_answer = main_answer.strip()
    # Log Q/A immediately with 'Pending' feedback
    log_interaction(
        sheet,
        st.session_state.user_email,
        st.session_state.last_question,
        st.session_state.last_answer,
        "Pending"
    )

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
            st.warning("Sorry I'm unable to answer your question. Please contact hr@providencehealth.bc.com for further assistance.")
            log_interaction(
                sheet,
                st.session_state.user_email,
                st.session_state.last_question,
                st.session_state.last_answer,
                "No"
            )
            st.session_state.last_answer = None  # Reset