import streamlit as st
import base64
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("Please set the GROQ_API_KEY in your .env file.")
    st.stop()

# Function to encode the image
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Function to generate captions for images
def generate_caption(uploaded_image):
    try:
        base64_image = encode_image(uploaded_image)
         url = "https://api.x.ai/v1/chat/completions"  # Corrected API endpoint
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "grok-vision",  # Corrected model name
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        st.error(f"Error generating caption: {str(e)}")
        return None

# Function to generate chat responses with streaming
def generate_chat_response(prompt, history=[]):
    try:
        url = "https://api.groq.com/v1/chat/completions"  # Corrected API endpoint
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            *history,
            {"role": "user", "content": prompt},
        ]
        data = {
            "model": "grok-latest",  # Corrected model name
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
        }

        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        # Stream the response
        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    chunk = json.loads(decoded_line[6:])
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        full_response += delta
                        yield delta
        yield full_response

    except Exception as e:
        st.error(f"Error generating chat response: {str(e)}")

# Streamlit App
st.title("Groq Vision & Chat App")

# Image Captioning Section
st.subheader("Image Captioning")
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    if st.button("Generate Caption"):
        with st.spinner("Generating caption..."):
            caption = generate_caption(uploaded_file)
            if caption:
                st.success("Caption Generated!")
                st.write("**Caption:**", caption)

# Chat Section
st.subheader("Chat with Groq")
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
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
