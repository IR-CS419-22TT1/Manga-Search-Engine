import json
import streamlit as st
from dotenv import load_dotenv
import os

st.set_page_config(page_title="Manga Retrieval", page_icon=":material/edit:")

# Load .env file
load_dotenv()

@st.cache_resource
def get_img():
    print("Loading images...")
    with open('./assets/img_map.json', 'r') as f:
        index = json.load(f)
    return index

index = get_img()

st.session_state.index = index

sidebar_pg = f"""
<style>
[data-testid="stSidebarNav"] {{
border-radius: 20px;
padding: 10px;
background-color: white;
margin: 10px;
}}
[data-testid="stSidebarUserContent"] {{
border-radius: 20px;
padding: 15px;
background-color: white;
margin: 5px;
}}
[data-testid="stSidebarCollapseButton"] {{
border-radius: 5px;
background-color: white;
}}
</style>
"""
st.markdown(sidebar_pg, unsafe_allow_html=True)
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

scene_search = st.Page("multimodal_search.py", title="Scene Search", icon="🔍")
dialogue_search = st.Page("dialogue_search.py", title="Dialogue Search", icon="💬")

pg = st.navigation([scene_search, dialogue_search])
pg.run()