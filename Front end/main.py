import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from utils import ClientFactory
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from search import SearchEngine

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
    
# Configure the generative AI client
genai.configure(api_key=api_key)
# Register and create the Google generative AI client
client_factory = ClientFactory()
client_factory.register_client('google', genai.GenerativeModel)

# Initialize Chroma DB client and collections
db_path = "database"  # Add your db path here
client = chromadb.PersistentClient(path=db_path)
embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()

visual_collection = client.get_or_create_collection(
    name='multimodal_collection',
    embedding_function=embedding_function,
    data_loader=data_loader
)

caption_collection = client.get_or_create_collection(
    name='caption_collection',
    embedding_function=embedding_function
)

# Ensure temp_images directory exists
if not os.path.exists("temp_images"):
    os.makedirs("temp_images")

search_engine = SearchEngine(
        index_path="index.json",
        stopwords_path="./english-stopwords.txt"
    )

st.session_state.client_factory = client_factory
st.session_state.visual_collection = visual_collection
st.session_state.caption_collection = caption_collection
st.session_state.search_engine = search_engine

scene_search = st.Page("multimodal_search.py", title="Scene Search", icon="🔍")
dialogue_search = st.Page("dialogue_search.py", title="Dialogue Search", icon="💬")

pg = st.navigation([scene_search, dialogue_search])
pg.run()