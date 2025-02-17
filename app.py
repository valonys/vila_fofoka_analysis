import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import pandas as pd
from io import BytesIO

# Load environment variables
load_dotenv()

# Set up API Key
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("API_KEY missing from .env file")
    st.stop()

# Configure UI
st.markdown("""
    <style>
    @import url('https://fonts.cdnfonts.com/css/tw-cen-mt');
    * { font-family: 'Tw Cen MT', sans-serif; }
    </style>
    """, unsafe_allow_html=True)
st.title("🚀 ValNerdzx 🚀")

# File upload in sidebar
with st.sidebar:
    st.header("📁 Upload Documents")
    uploaded_file = st.file_uploader("", type=["pdf", "docx", "xlsx", "xlsm"])

# Session state for file context
if "file_context" not in st.session_state:
    st.session_state.file_context = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def parse_file(file):
    """Process uploaded file and return text content"""
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                      "application/vnd.ms-excel"]:
        df = pd.read_excel(file)
        return df.to_string()
    return None

# Process file but don't display until requested
if uploaded_file and not st.session_state.file_context:
    st.session_state.file_context = parse_file(uploaded_file)
    st.sidebar.success("✅ File ready for analysis")

def generate_response(prompt):
    """Generate AI response with file context awareness"""
    messages = [{
        "role": "system",
        "content": f"You are ValNerdzx. Analyze documents and answer questions. Current document:\n{st.session_state.file_context}"
    } if st.session_state.file_context else {
        "role": "system",
        "content": "You are ValNerdzx. Provide helpful responses."
    }]
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        start = time.time()
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "
