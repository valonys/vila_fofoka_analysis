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

        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes

        # Stream the response
        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    try:
                        chunk = json.loads(decoded_line[6:])  # Remove "data: " prefix
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            full_response += delta
                            yield delta
                    except json.JSONDecodeError as e:
                        st.error(f"Error decoding JSON: {str(e)}")
                        st.error(f"Received data: {decoded_line}")
                        yield None
        yield full_response

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        yield None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        yield None

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
