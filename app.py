import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

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

# Function to generate chat responses
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
            "stream": False,
            "temperature": 0
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']

    except Exception as e:
        st.error(f"Error generating chat response: {str(e)}")
        return None

# Streamlit App
st.title("English Tutor Chat App")

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

    # Generate chat response
    history = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]
    response = generate_chat_response(prompt, history)

    if response:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
