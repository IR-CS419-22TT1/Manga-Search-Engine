import streamlit as st
import numpy as np
from PIL import Image
from utils import consolidate_results
import os
from utils import vector_for_interactive_search
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

# Ensure the OpenCLIPEmbeddingFunction is initialized
embedding_function = OpenCLIPEmbeddingFunction()

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

if st.button("Search"):
    results = {}
    final_caption = ""
    text_caption = ""
    image_caption = ""
    
    st.session_state.only_one_image_no_text = False
    
    # Case 1: Only 1 image is uploaded and no text input
    if len(image_files) == 1 and not any(st.session_state.text_inputs):
        st.session_state.only_one_image_no_text = True
        image = image_files[0]
        try:
        # Convert the uploaded image to a numpy array
            img = Image.open(image).convert("RGB")
            img_array = np.array(img)

            # Define the updated system content for generating individual descriptions
            system_content_individual = """
            You are an assistant specializing in analyzing images. Your task is to generate a concise caption for the given image. Focus on identifying key subjects (e.g., names of characters, objects), their appearance, and their context. Avoid unnecessary details that do not contribute to understanding the main subject or action.
            """
            # Generate individual image descriptions
            client_kwargs_individual = {
                "model_name": model_name,
                "generation_config": {
                    "temperature": 0.7,
                },
                "system_instruction": system_content_individual,
            }
            if st.session_state.client_factory:
                client_individual = st.session_state.client_factory.create_client('google', **client_kwargs_individual)
                
            user_content_individual = "Generate a concise caption for the following image, focusing on key subjects, name of characters, their appearance, and the context."
            response = client_individual.generate_content([user_content_individual, img], stream=True)
            response.resolve()
            description = response.text.strip()

            try:
                # Generate embedding for the final_caption text
                final_caption_embedding = embedding_function([description])  # Pass as a list
                # Store the query vector in session state
                st.session_state.query_vector = final_caption_embedding
            except Exception as e:
                st.error(f"Error generating embedding for final_caption: {e}")
                
            # Query the collections
            image_results_visual = st.session_state.visual_collection.query(query_images=[img_array], n_results=10, include=["distances", "embeddings"])

            image_results_caption = st.session_state.caption_collection.query(query_texts=[description], n_results=10, include=["distances", "embeddings"])
            
            consolidated_image_results = consolidate_results(image_results_visual, image_results_caption)

            results = consolidated_image_results
        except Exception as e:
            st.error(f"Error processing image {image.name}: {e}")
    else:
        st.session_state.only_one_image_no_text = False
            
    if any(st.session_state.text_inputs) and not st.session_state.only_one_image_no_text:
        # Combine all text inputs into a single string using generative AI
        gathered_text = " ".join([t for t in st.session_state.text_inputs if t])
        # Update system and user content for the generative model
        system_content = """
        You are an assistant specializing in combining search phrases. Your task is to interpret multiple related phrases, focusing on identifying key subjects(e.g., names of characters, objects), relationships, and actions. The combined query must be concise, relevant, and meaningful for searching databases.
        """
        
        user_content = f"""
        Combine the following search phrases into a single, meaningful query that clearly conveys the names of characters, relationships and actions described:
        {gathered_text}
        """
        # Generate consolidated query using generative AI
        try:
            client_kwargs = {
                "model_name": model_name,
                "generation_config": {
                    "temperature": 0.7,
                },
                "system_instruction": system_content,
            }
            client = st.session_state.client_factory.create_client('google', **client_kwargs)

            response = client.generate_content(user_content)
            consolidated_query = response.text.strip()
            st.write(f"Consolidated Query: {consolidated_query}")  # Display the combined query for debugging

            # Update text caption for the consolidated query
            text_caption = consolidated_query

        except Exception as e:
            st.error(f"Error consolidating text inputs: {e}")
    
    if any(image_files) and not st.session_state.only_one_image_no_text:
        gathered_images = []
        for image in image_files:
            if image:
                try:
                    img = Image.open(image).convert("RGB")  # Keep the image as PIL format
                    gathered_images.append(img)
                except Exception as e:
                    st.error(f"Error processing image {image.name}: {e}")
        if gathered_images:
            try:
                # Define the updated system content for generating individual descriptions
                system_content_individual = """
                You are an assistant specializing in analyzing images. Your task is to generate a concise caption for the given image. Focus on identifying key subjects (e.g., names of characters, objects), their appearance, and their context. Avoid unnecessary details that do not contribute to understanding the main subject or action.
                """
                
                # Define the updated system content for consolidating the descriptions
                system_content_combined = """
                You are an assistant specializing in combining image captions. Your task is to consolidate multiple related captions into a single, coherent caption. Focus on identifying the common themes, key characters, names of characters, their actions, and their relationships. The final caption should be concise, descriptive, and suitable for searching databases.
                """

                # Step 1: Generate individual image descriptions
                individual_descriptions = []
                for img in gathered_images:
                    client_kwargs_individual = {
                        "model_name": model_name,
                        "generation_config": {
                            "temperature": 0.7,
                        },
                        "system_instruction": system_content_individual,
                    }
                    client_individual = st.session_state.client_factory.create_client('google', **client_kwargs_individual)

                    user_content_individual = "Generate a concise caption for the following image, focusing on key subjects, names of characters, their appearance, and the context."
                    response = client_individual.generate_content([user_content_individual, img], stream=True)
                    response.resolve()
                    description = response.text.strip()
                    individual_descriptions.append(description)

                # Step 2: Consolidate individual descriptions into a single caption
                client_kwargs_combined = {
                    "model_name": model_name,
                    "generation_config": {
                        "temperature": 0.7,
                    },
                    "system_instruction": system_content_combined,
                }
                client_combined = st.session_state.client_factory.create_client('google', **client_kwargs_combined)

                user_content_combined = f"""
                Combine the following captions into a single, meaningful caption, focusing on common themes, key characters, names of characters, their actions, and relationships:
                {'. '.join(individual_descriptions)}
                """
                response_combined = client_combined.generate_content(user_content_combined, stream=True)
                response_combined.resolve()
                consolidated_caption = response_combined.text.strip()
                st.write(f"Consolidated Caption: {consolidated_caption}")  # Display the caption for debugging

                # Update image caption for the consolidated caption
                image_caption = consolidated_caption

            except Exception as e:
                st.error(f"Error consolidating image inputs: {e}")

    # Combine text and image captions if both exist
    if text_caption and image_caption:
        try:
            system_content_combine = """
            You are an assistant specializing in combining textual descriptions and image analyses. Your task is to take a textual query and an image caption, identify the key characters, names of characters and their relationships, and generate a single, meaningful caption. Focus on interpreting the intent of the text query and linking it with the image subject to create a relevant and concise description for searching databases.
            """
            
            user_content_combine = f"""
            Combine the following textual query and image caption into a single, meaningful caption. Focus on identifying key characters, names of characters, their actions, and relationships:
            Text Query: {text_caption}
            Image Caption: {image_caption}
            """

            client_kwargs_combine = {
                "model_name": model_name,
                "generation_config": {
                    "temperature": 0.7,
                },
                "system_instruction": system_content_combine,
            }
            client_combine = st.session_state.client_factory.create_client('google', **client_kwargs_combine)

            response_combine = client_combine.generate_content(user_content_combine, stream=True)
            response_combine.resolve()
            final_caption = response_combine.text.strip()
            st.write(f"Final Caption: {final_caption}")  # Display the final caption for debugging
        except Exception as e:
            st.error(f"Error combining text and image captions: {e}")
    elif text_caption:
        final_caption = text_caption
    elif image_caption:
        final_caption = image_caption
    
    # Query the database using the final caption
    if final_caption:
        try:
            # Generate embedding for the final_caption text
            final_caption_embedding = embedding_function([final_caption])  # Pass as a list
            # Store the query vector in session state
            st.session_state.query_vector = final_caption_embedding
        except Exception as e:
            st.error(f"Error generating embedding for final_caption: {e}")
        # Query both databases using the final caption
        results_visual = st.session_state.visual_collection.query(query_texts=[final_caption], n_results=10, include=["distances", "embeddings"])
        results_caption = st.session_state.caption_collection.query(query_texts=[final_caption], n_results=10, include=["distances", "embeddings"])

        # Consolidate and rank the results
        consolidated_results = consolidate_results(results_visual, results_caption)
        results = consolidated_results
    # Display results
    if results:
        # Store results in session state
        st.session_state.results = results
        st.session_state.selected_images = [False] * len(results)
        st.session_state.refine_results = False
        only_one_image_no_text = False

# Display Results
if "results" in st.session_state and st.session_state.results:
    # Header with "Refine Results" button
    col_subheader, col_button = st.columns([3, 1])
    with col_subheader:
        st.subheader("Top 10 Results")
    with col_button:
        # Enable "Refine Results" only if checkboxes are selected
        if "selected_images" not in st.session_state or len(st.session_state.selected_images) != len(st.session_state.results):
            st.session_state.selected_images = [False] * len(st.session_state.results)

        refine_disabled = not any(st.session_state.selected_images)
        st.session_state.refine_results = not refine_disabled
        
        # Refine Results Button Logic
        if st.button("Refine Results", disabled=not st.session_state.refine_results):
            print('state of images: ', st.session_state.selected_images)
            try:
                results = st.session_state.results

                # Extract the embedding vector for the final caption
                final_caption_embedding = st.session_state.query_vector

                # Ensure the embedding is a plain list of floats
                if isinstance(final_caption_embedding, list) and isinstance(final_caption_embedding[0], np.ndarray):
                    final_caption_embedding = final_caption_embedding[0].tolist()  # Flatten
                elif isinstance(final_caption_embedding, np.ndarray):
                    final_caption_embedding = final_caption_embedding.tolist()
                else:
                    st.error("Unexpected embedding format")
                    st.stop()

                # Convert to numpy array for further calculations
                initial_query_vector = np.array(final_caption_embedding)

                # Collect positive (unticked) and negative (ticked) vectors
                positive_vectors = []
                negative_vectors = []  # Collect all negative vectors

                for idx, (res_id, is_negative) in enumerate(zip(results.keys(), st.session_state.selected_images)):
                    distance, embedding = results[res_id]  # Extract distance and embedding

                    # Convert embedding to numpy array
                    embedding = np.array(embedding)

                    if is_negative:  # Negative images (ticked)
                        negative_vectors.append(embedding)
                    else:  # Positive images (unticked)
                        positive_vectors.append(embedding)

                # Ensure we have at least one valid negative vector
                if not negative_vectors:
                    st.error("No negative images selected. Please select at least one negative image.")
                    st.stop()

                # Calculate the refined query vector using the interactive search function
                new_query_vector = vector_for_interactive_search(
                    initial_query=initial_query_vector,
                    positive_vectors=positive_vectors,
                    negative_vectors=negative_vectors
                )

                results_visual = None
                results_caption = None

                if st.session_state.only_one_image_no_text:
                    image = image_files[0]
                    img = Image.open(image).convert("RGB")
                    img_array = np.array(img)
                    # Query the collections
                    results_visual = st.session_state.visual_collection.query(
                        query_images=[img_array], 
                        n_results=10, 
                        include=["distances", "embeddings"]
                    )

                    results_caption = st.session_state.caption_collection.query(
                        query_embeddings=[new_query_vector.tolist()],
                        n_results=10,
                        include=["distances", "embeddings"]
                    )
                else:
                    # Query both databases with the refined query vector
                    results_visual = st.session_state.visual_collection.query(
                        query_embeddings=[new_query_vector.tolist()],  # Convert back to list
                        n_results=10,
                        include=["distances", "embeddings"]
                    )

                    results_caption = st.session_state.caption_collection.query(
                        query_embeddings=[new_query_vector.tolist()],
                        n_results=10,
                        include=["distances", "embeddings"]
                    )

                # Consolidate results from both queries
                consolidated_results = consolidate_results(results_visual, results_caption)

                # Update session state with consolidated results
                st.session_state.results = consolidated_results
                st.session_state.selected_images = [False] * len(consolidated_results)
                st.session_state.refine_results = False
                st.session_state.query_vector = new_query_vector  # Update the query vector

                st.success("Results refined successfully!")

            except Exception as e:
                st.error(f"Error refining results: {e}")

    # Display results with checkboxes
    columns_per_row = 3
    result_ids = list(st.session_state.results.keys())  # Extract result IDs

    for row_start in range(0, len(result_ids), columns_per_row):
        cols = st.columns(columns_per_row)
        for idx, col in enumerate(cols):
            result_idx = row_start + idx
            if result_idx >= len(result_ids):
                break  # Exit loop if there are no more results

            res_id = result_ids[result_idx]
            dist, _ = st.session_state.results[res_id]  # Extract distance and embedding

            # Generate the image path based on the result ID
            image_path = res_id.replace("caption", "dataset").replace("txt", "png").replace("_", "/")
            image_path = "./" + image_path

            with col:
                # Checkbox for image selection
                selected = st.checkbox(
                    "Select",
                    key=f"checkbox_{result_idx}",
                    value=st.session_state.selected_images[result_idx]
                )
                st.session_state.selected_images[result_idx] = selected

                # Display image with the distance caption
                st.image(image_path, caption=f"{os.path.basename(image_path)} (Distance: {dist:.4f})")