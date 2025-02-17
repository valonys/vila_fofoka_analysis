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

# Load environment variables from .env file
load_dotenv()

# Set up API Key
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("Please set the API_KEY in your .env file.")
    st.stop()

# Define the endpoint and headers
url = "https://api.x.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Custom CSS for Tw Cen MT font
st.markdown(
    """
    <style>
    @import url('https://fonts.cdnfonts.com/css/tw-cen-mt');
    html, body, [class*="css"] {
        font-family: 'Tw Cen MT', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title with rocket emojis
st.title("🚀 ValNerdzx 🚀")

# Sidebar for file upload
st.sidebar.header("Upload Files")
uploaded_file = st.sidebar.file_uploader(
    "Upload a file", type=["pdf", "docx", "xlsx", "xlsm"]
)

# Function to read uploaded files
@st.cache_data
def read_file(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
        df = pd.read_excel(file)
        return df.to_string()
    else:
        return "Unsupported file type."

# Display file content
if uploaded_file:
    file_content = read_file(uploaded_file)
    st.sidebar.subheader("File Content")
    st.sidebar.write(file_content)

# Function to generate chat responses with streaming
def generate_chat_response(prompt, history=[]):
    try:
        messages = [
            {"role": "system", "content": "You are a top-notch English tutor, guide me appropriately"},
            *history,
            {"role": "user", "content": prompt},
        ]
        data = {
            "model": "grok-beta",
            "messages": messages,
            "stream": True,  # Enable streaming
            "temperature": 0
        }

        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        # Stream the response
        full_response = ""
        token_count = 0
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    chunk_data = decoded_line[6:]  # Remove "data: " prefix
                    if chunk_data == "[DONE]":
                        # End of stream
                        break
                    try:
                        chunk = json.loads(chunk_data)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            full_response += delta
                            token_count += len(delta.split())  # Approximate token count
                            yield delta
                    except json.JSONDecodeError as e:
                        st.error(f"Error decoding JSON: {str(e)}")
                        st.error(f"Received data: {chunk_data}")
                        yield None

        end_time = time.time()
        processing_speed = token_count / (end_time - start_time)  # Tokens per second
        cost = token_count * 0.00002  # Example cost calculation ($0.00002 per token)

        yield f"\n\n**Tokens:** {token_count} | **Speed:** {processing_speed:.2f} tokens/sec | **Cost:** ${cost:.4f}"

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        yield None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        yield None

# Chat Section
st.subheader("Chat with the English Tutor")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    avatar = "🤖" if message["role"] == "assistant" else "👨‍💻"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your message..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👨‍💻"):
        st.markdown(prompt)

    # Generate chat response with streaming
    history = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]
    response_generator = generate_chat_response(prompt, history)

    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response_generator:
            if chunk:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
