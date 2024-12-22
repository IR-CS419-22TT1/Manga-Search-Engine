import streamlit as st
from dotenv import load_dotenv
import os
import requests  # Import requests for API calls

REGISTER_USER_API_URL = "http://127.0.0.1:5000/register-user"

st.set_page_config(page_title="Manga Retrieval", page_icon=":material/edit:")

# Load .env file
load_dotenv()

# Sidebar input for API key
st.sidebar.title("Gemini API 🔑")

# Check if API key is already in .env
default_api_key = os.getenv("GEMINI_API_KEY", "")
model_name = "gemini-1.5-flash"

# Text input for API key
api_key = st.sidebar.text_input(
    "Enter Key",
    value=default_api_key,
    type="password",
    help="You can enter your Gemini API key here or set it in a .env file"
)

# Store the API key in session state
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = api_key

# Update API key if user enters a new one
if api_key:
    st.session_state.gemini_api_key = api_key

# Call backend API to register user and store the id
if "session_state_id_turn" not in st.session_state:
    try:
        response = requests.post(REGISTER_USER_API_URL)
        if response.status_code == 201:
            st.session_state.session_state_id_turn = response.json().get("user_id")
            # st.success(f"User registered with ID: {st.session_state.session_state_id_turn}")
        else:
            st.error(f"Error registering user: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {e}")

scene_search = st.Page("multimodal_search.py", title="Scene Search", icon="🔍")
dialogue_search = st.Page("dialogue_search.py", title="Dialogue Search", icon="💬")

pg = st.navigation([scene_search, dialogue_search])
pg.run()