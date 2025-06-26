import time
import os
import joblib
import streamlit as st
import google.generativeai as genai

# 🔐 Hardcoded API Key (replace this!)
GOOGLE_API_KEY = "enter your api key"

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY is missing.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(
    page_title="AI POWERED CHATBOT",
    layout="wide", 
    page_icon="❓"
)

# Hide Streamlit UI elements
st.markdown("""
<style>
.stDeployButton, #MainMenu, footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

os.makedirs('data/', exist_ok=True)

# Load previous chats
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

# Sidebar
st.sidebar.header("Configuration for the System", divider="rainbow")

with st.sidebar:
    st.write('### Previous Gemini Chat')
    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            'Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
        )
    else:
        st.session_state.chat_id = st.selectbox(
            'Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
        )
    st.session_state.chat_title = f'Gemini-Chat-{st.session_state.chat_id}'

st.title("AI POWERED CHATBOT✨")
st.subheader("Ask anything and get answers in real-time.", divider="rainbow")

# Load message history
try:
    st.session_state.messages = joblib.load(f'data/{st.session_state.chat_id}-st_messages')
    st.session_state.gemini_history = joblib.load(f'data/{st.session_state.chat_id}-gemini_messages')
except:
    st.session_state.messages = []
    st.session_state.gemini_history = []

# Settings
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.75, 0.01)
max_new_tokens = st.sidebar.slider("Max Output Tokens", 128, 2048, 256, 16)

generation_config = {
    "temperature": temperature,
    "max_output_tokens": max_new_tokens,
    "top_p": 0.2,
    "top_k": 10,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Load Gemini model
st.session_state.model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config=generation_config,
    safety_settings=safety_settings,
)

st.session_state.chat = st.session_state.model.start_chat(
    history=st.session_state.gemini_history
)

# Show past messages
for msg in st.session_state.messages:
    with st.chat_message(name=msg['role'], avatar=msg.get('avatar')):
        st.markdown(msg['content'])

# Chat input
if prompt := st.chat_input('Your message here...'):
    if st.session_state.chat_id not in past_chats:
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')

    with st.chat_message('user'):
        st.markdown(prompt)

    st.session_state.messages.append({
        'role': 'user',
        'content': prompt,
    })

    response = st.session_state.chat.send_message(prompt, stream=True)

    with st.chat_message(name=MODEL_ROLE, avatar=AI_AVATAR_ICON):
        placeholder = st.empty()
        full_response = ''
        for chunk in response:
            for ch in chunk.text.split(' '):
                full_response += ch + ' '
                time.sleep(0.05)
                placeholder.write(full_response + '▌')
        placeholder.write(full_response)

    st.session_state.messages.append({
        'role': MODEL_ROLE,
        'content': st.session_state.chat.history[-1].parts[0].text,
        'avatar': AI_AVATAR_ICON,
    })

    st.session_state.gemini_history = st.session_state.chat.history
    joblib.dump(st.session_state.messages, f'data/{st.session_state.chat_id}-st_messages')
    joblib.dump(st.session_state.gemini_history, f'data/{st.session_state.chat_id}-gemini_messages')
