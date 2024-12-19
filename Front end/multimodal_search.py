import streamlit as st
import numpy as np
from PIL import Image
import os
import requests
import io
from io import BytesIO

# Backend API endpoint
BACKEND_API_URL = "http://127.0.0.1:5000/upload-image"  # Update with your backend URL
SEARCH_SCENE_API_URL = "http://127.0.0.1:5000/search-scene"
GET_IMAGE_API_URL = "http://127.0.0.1:5000/get-image"

# Check for API key
if "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
    st.sidebar.success("✅ API Key is entered!")
else:
    st.sidebar.error("⚠️ No API key detected! Please set it on the main page.")
    
model_name = "gemini-1.5-flash"

col1, col2 = st.columns([1, 3])  # Adjust column width ratios as needed
# Add the image in the first column
with col1:
    st.image('./assets/app_logo.png', width=200)
# Divide col2 into three rows
with col2:
    row1, row2, row3 = st.columns(1), st.columns(1), st.columns(1)
    with row1[0]:
        st.empty()  # Leave the first row empty
    with row2[0]:
        st.empty()  # Leave the third row empty
    with row3[0]:
        st.title("Multimodal Scene Search")  # Add the title to the second row

st.info("Type **descriptions** or upload **images** you want to search 💖")
with open('./style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)\
    
if "text_inputs" not in st.session_state:
    st.session_state.text_inputs = [""]

def add_text_input():
    st.session_state.text_inputs.append("")

# Search bar
for i, text_input in enumerate(st.session_state.text_inputs):
    st.session_state.text_inputs[i] = st.text_input(
        label=f"Description {i+1}", 
        value=text_input, 
        key=f"description_{i+1}")
    
if st.button("Add description"):
    add_text_input()

# Image uploader
image_files = st.file_uploader(
    label="Images:",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True)

uploaded_paths = []

# Function to upload image to the backend API
def upload_image_to_backend(image_file):
    try:
        # Convert Streamlit UploadedFile to file-like object
        file_buffer = io.BytesIO(image_file.read())
        file_buffer.name = image_file.name  # Set the name for the file
        files = {"file": (image_file.name, file_buffer, image_file.type)}
        
        # Call the API
        response = requests.post(BACKEND_API_URL, files=files)
        
        # Check for success
        if response.status_code == 201:
            # st.success(f"Image '{image_file.name}' uploaded successfully!")
            return response.json()  # Return the backend's response (e.g., saved file path)
        else:
            st.error(f"Failed to upload '{image_file.name}': {response.text}")
    except Exception as e:
        st.error(f"Error uploading image '{image_file.name}': {e}")
    return None

# Process uploaded images
if image_files:
    for image_file in image_files:
        response = upload_image_to_backend(image_file)
        if response:
            uploaded_paths.append(response.get("image_path"))  # Collect the saved paths if provided

# Session State Initialization
if "results" not in st.session_state:
    st.session_state.results = []

if "selected_images" not in st.session_state:
    st.session_state.selected_images = []

if "refine_results" not in st.session_state:
    st.session_state.refine_results = False

if "query_vector" not in st.session_state:
    st.session_state.query_vector = None

if "only_one_image_no_text" not in st.session_state:
    st.session_state.only_one_image_no_text = False

# Function to call the search-scene API
def call_search_scene_api(image_paths, text_inputs, top_k):
    payload = {
        "image_path": image_paths,
        "text": text_inputs,
        "top_k": top_k
    }
    try:
        response = requests.post(SEARCH_SCENE_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()["results"]
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Failed to call API: {e}")
    return []

# Function to fetch an image from the backend
def fetch_image_from_backend(image_path):
    try:
        response = requests.get(f"{GET_IMAGE_API_URL}/{image_path}", stream=True)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            st.error(f"Failed to fetch image: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching image: {e}")
    return None

if st.button("Search"):
    results = {}
    final_caption = ""
    text_caption = ""
    image_caption = ""
    
    # Case 1: Only 1 image is uploaded and no text input
    if len(image_files) == 1 and not any(st.session_state.text_inputs):
        # st.write('Case only one image no text', uploaded_paths)
        st.session_state.only_one_image_no_text = True
        results = call_search_scene_api(image_paths=uploaded_paths, text_inputs=st.session_state.text_inputs, top_k=10)
        # Display results
        if results:
            st.subheader("Search Results")
            columns_per_row = 3
            for row_start in range(0, len(results), columns_per_row):
                cols = st.columns(columns_per_row)
                for col, result in zip(cols, results[row_start:row_start + columns_per_row]):
                    image_path = f"{result['manga']}/{result['page_type']}/{result['page_number']}.png"
                    image = fetch_image_from_backend(image_path)

                    with col:
                        if image:
                            st.image(image, caption=f"{result['manga']} - {result['page_type']} - {result['page_number']}")
        else:
            st.warning("No results found.")
    else:
        st.session_state.only_one_image_no_text = False
            
    if not st.session_state.only_one_image_no_text:
        # st.write('Case multiple images or text', st.session_state.text_inputs)
        results = call_search_scene_api(image_paths=uploaded_paths, text_inputs=st.session_state.text_inputs, top_k=10)
        # Display results
        if results:
            st.subheader("Search Results")
            columns_per_row = 3
            for row_start in range(0, len(results), columns_per_row):
                cols = st.columns(columns_per_row)
                for col, result in zip(cols, results[row_start:row_start + columns_per_row]):
                    image_path = f"{result['manga']}/{result['page_type']}/{result['page_number']}.png"
                    image = fetch_image_from_backend(image_path)

                    with col:
                        if image:
                            st.image(image, caption=f"{result['manga']} - {result['page_type']} - {result['page_number']}")
        else:
            st.warning("No results found.")