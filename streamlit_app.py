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