import streamlit as st

st.title("MN Statutes Chatbot")
prompt = st.chat_input("Ask about MN Statute 504B...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    response = "According to MN Law..." 
    
    with st.chat_message("assistant"):
        st.write(response)