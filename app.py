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

# Configure Avatars (using raw GitHub URLs)
USER_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/9904d9a0d445ab0488cf7395cb863cce7621d897/USER_AVATAR.png"
#BOT_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/c4c5c8d8ead5831178cb213fc82a22f5cb8abae6/BOT_AVATAR.jpg"
BOT_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/991f4c6e4e1dc7a8e24876ca5aae5228bcdb4dba/Ataliba_Avatar.jpg"

# Configure UI
st.markdown("""
    <style>
    @import url('https://fonts.cdnfonts.com/css/tw-cen-mt');
    * { font-family: 'Tw Cen MT', sans-serif; }
    </style>
    """, unsafe_allow_html=True)
st.title("🚀 Ataliba the Nerdzx Agent🚀")

# File upload in sidebar
with st.sidebar:
    st.header("📁 Upload Documents")
    uploaded_file = st.file_uploader("", type=["pdf", "docx", "xlsx", "xlsm"])

# Session state initialization
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

# Process file upload
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
                "model": "grok-beta",
                "messages": messages,
                "temperature": 0.3,
                "stream": True
            },
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = line.decode("utf-8").replace("data: ", "")
                if chunk == "[DONE]": break
                try:
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content", "")
                    full_response += delta
                    yield delta
                except:
                    continue
        
        # Calculate metrics
        #tokens = len(full_response.split())
        #speed = tokens / (time.time() - start)
        #yield f"\n\n🔑 Tokens: {tokens} | 🚀 Speed: {speed:.1f}t/s | 💵 Cost: ${tokens*0.00002:.4f}"
        # Calculate metrics
        input_tokens = len(prompt.split())  # Assuming 'input_text' is the variable holding the user's input
        output_tokens = len(full_response.split())  # 'full_response' is the chatbot's response

        # Calculate costs based on grok-beta pricing
        input_cost = (input_tokens / 1000000) * 5
        output_cost = (output_tokens / 1000000) * 15
        total_cost_usd = input_cost + output_cost
        # Convert to AOA
        exchange_rate = 1.16
        total_cost_aoa = total_cost_usd * exchange_rate

        # Calculate speed
        speed = output_tokens / (time.time() - start)

        yield f"\n\n🔑 Input Tokens: {input_tokens} | Output Tokens: {output_tokens} | 🚀 Speed: {speed:.1f}t/s | 💵 Cost (USD): ${total_cost_usd:.4f} | 💵 Cost (AOA): {total_cost_aoa:.4f}"
        
    except Exception as e:
        yield f"❌ Error: {str(e)}"

# Chat interface
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=USER_AVATAR if msg["role"] == "user" else BOT_AVATAR):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about your document..."):
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):  # Avatar applied here
        st.markdown(prompt)

    # Generate and stream response
    with st.chat_message("assistant", avatar=BOT_AVATAR):  # Avatar applied here
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in generate_response(prompt):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
