import streamlit as st
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from PIL import Image
import numpy as np
import os
from dotenv import load_dotenv
import google.generativeai as genai
from search import SearchEngine

# Load environment variables from .env file
load_dotenv(override=True)

# Set the API key and Gemini model name directly in the code
api_key = os.getenv('GEMINI_API_KEY')  # Replace with your actual API key
model_name = "gemini-1.5-flash"

# Ensure the API key is set
if not api_key:
    raise ValueError("API_KEY must be set.")

# Configure the generative AI client
genai.configure(api_key=api_key)

# ClientFactory class to manage API clients
class ClientFactory:
    def __init__(self):
        self.clients = {}
    
    def register_client(self, name, client_class):
        self.clients[name] = client_class
    
    def create_client(self, name, **kwargs):
        client_class = self.clients.get(name)
        if client_class:
            return client_class(**kwargs)
        raise ValueError(f"Client '{name}' is not registered.")

# Register and create the Google generative AI client
client_factory = ClientFactory()
client_factory.register_client('google', genai.GenerativeModel)

def consolidate_results(results1, results2):
    """Consolidates results from two collections based on summed distances."""
    combined_results = {}

    for ids, distances in zip(results1['ids'][0], results1['distances'][0]):
        combined_results[ids] = distances

    for ids, distances in zip(results2['ids'][0], results2['distances'][0]):
        if ids in combined_results:
            combined_results[ids] += distances
        else:
            combined_results[ids] = distances

    # Sort results by summed distances
    sorted_results = sorted(combined_results.items(), key=lambda x: x[1])
    return sorted_results[:10]

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

ocr_collection = client.get_or_create_collection(
    name='ocr_collection',
    embedding_function=embedding_function
)

# Ensure temp_images directory exists
if not os.path.exists("temp_images"):
    os.makedirs("temp_images")

search_engine = SearchEngine(
            index_path="index.json",
            stopwords_path="./english-stopwords.txt"
        )

# Page Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Input Data", "Search"])

if page == "Input Data":
    st.title("Input Data")

    # Dynamic input fields
    text_inputs = []
    image_inputs = []

    if 'text_count' not in st.session_state:
        st.session_state.text_count = 1
    if 'image_count' not in st.session_state:
        st.session_state.image_count = 1

    for i in range(st.session_state.text_count):
        text_inputs.append(st.text_input(f"Text Input {i+1}", key=f"text_input_{i}"))

    for i in range(st.session_state.image_count):
        image_inputs.append(st.file_uploader(f"Image Input {i+1}", type=["png", "jpg", "jpeg"], key=f"image_input_{i}"))

    if st.button("Add Text Input"):
        st.session_state.text_count += 1

    if st.button("Add Image Input"):
        st.session_state.image_count += 1

    if st.button("Submit Inputs"):
        results = {}
        final_caption = ""
        text_caption = ""
        image_caption = ""
        only_one_image_no_text = False

        if len(image_inputs) == 1 and not any(text_inputs):
            only_one_image_no_text = True
            image = image_inputs[0]  # Since there's exactly one image
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
                client_individual = client_factory.create_client('google', **client_kwargs_individual)

                user_content_individual = "Generate a concise caption for the following image, focusing on key subjects, name of characters, their appearance, and the context."
                response = client_individual.generate_content([user_content_individual, img], stream=True)
                response.resolve()
                description = response.text.strip()
                st.write(f"Image Caption: {description}")  # Display the caption for debugging

                # Query the collections
                image_results_visual = visual_collection.query(query_images=[img_array], n_results=10, include=["distances"])
                image_results_caption = caption_collection.query(query_texts=[description], n_results=10, include=["distances"])
                consolidated_image_results = consolidate_results(image_results_visual, image_results_caption)

                results = consolidated_image_results

            except Exception as e:
                st.error(f"Error processing image {image.name}: {e}")

        if any(text_inputs) and not only_one_image_no_text:
            # Combine all text inputs into a single string using generative AI
            gathered_text = " ".join([t for t in text_inputs if t])

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
                client = client_factory.create_client('google', **client_kwargs)

                response = client.generate_content(user_content)
                consolidated_query = response.text.strip()
                st.write(f"Consolidated Query: {consolidated_query}")  # Display the combined query for debugging

                # Update text caption for the consolidated query
                text_caption = consolidated_query

            except Exception as e:
                st.error(f"Error consolidating text inputs: {e}")

        if any(image_inputs) and not only_one_image_no_text:
            # Gather all valid image inputs
            gathered_images = []
            for image in image_inputs:
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
                        client_individual = client_factory.create_client('google', **client_kwargs_individual)

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
                    client_combined = client_factory.create_client('google', **client_kwargs_combined)

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
                client_combine = client_factory.create_client('google', **client_kwargs_combine)

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
            # Query both databases using the final caption
            results_visual = visual_collection.query(query_texts=[final_caption], n_results=10, include=["distances"])
            results_caption = caption_collection.query(query_texts=[final_caption], n_results=10, include=["distances"])

            # Consolidate and rank the results
            consolidated_results = consolidate_results(results_visual, results_caption)
            results = consolidated_results

        # Display results
        if results:
            st.subheader("Top 10 Results")
            for res_id, dist in results:
                image_path = res_id.replace("caption", "dataset").replace("txt", "png").replace("_", "/")
                image_path = "./" + image_path  # Re-add the leading './' for relative paths
                st.image(image_path, caption=f"{os.path.basename(image_path)} (Distance: {dist:.4f}")
            only_one_image_no_text = False
        else:
            st.info("No results found. Please ensure you have provided valid inputs.")

elif page == "Search":
    st.title("Search")
    query = st.text_input("Enter your search query:")

    if st.button("Search"):
        if query:
            ocr_results = search_engine.search(query, top_k=10)
            print('Streamlit get: ',ocr_results)
            st.subheader("Top 10 OCR Search Results")

            for ocr_result in ocr_results:
                ocr_id = ocr_result['postId']
                st.write(f"ID: {ocr_id}")
                # Convert OCR ID to image path
                image_path = ocr_id.replace("ocr_result", "dataset")
                image_path = image_path+ ".png"
                image_path = "./" + image_path
                st.image(image_path, caption=f"{os.path.basename(image_path)}")
        else:
            st.warning("Please enter a query to search.")