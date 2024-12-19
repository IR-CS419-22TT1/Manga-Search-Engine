import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
import os
from tqdm import tqdm

# Initialize the database path and new collection name
db_path = "database"  # Same database path as before
client = chromadb.PersistentClient(path=db_path)

# Initialize the embedding function for ocrs using OpenCLIP
ocr_embedding_function = OpenCLIPEmbeddingFunction()

# Create or get a new collection for ocrs
ocr_collection = client.get_or_create_collection(
    name='ocr_collection',
    embedding_function=ocr_embedding_function
)

def add_ocrs_to_collection(ocr_folder_path):
    # Get all ocr files in the folder
    ocr_files = [os.path.join(ocr_folder_path, f) for f in os.listdir(ocr_folder_path) 
                     if os.path.isfile(os.path.join(ocr_folder_path, f))]

    for ocr_file in tqdm(ocr_files, desc="Embedding OCR and Adding to DB"):
        try:
            # Read the ocr text from the file
            with open(ocr_file, 'r', encoding='utf-8') as file:
                ocr = file.read().strip()

            # Create a unique ID for the ocr based on the file name
            formatted_id = ocr_file.replace("./", "").replace("/", "_").replace("\\", "_")

            # Add the ocr to the database collection
            ocr_collection.add(
                ids=[formatted_id],
                documents=[ocr]
            )
        except Exception as e:
            print(f"Error processing ocr file {ocr_file}: {e}")

# Path to the folder containing ocr files
# ocr_folder_path = "./ocr_text/onepiece/colored"
# ocr_folder_path = "./ocr_text/onepiece/grayscale"
# ocr_folder_path = "./ocr_text/blackclover/colored"
# ocr_folder_path = "./ocr_text/blackclover/grayscale"
# ocr_folder_path = "./ocr_text/bukonohero/colored"
ocr_folder_path = "./ocr_text/bukonohero/grayscale"

# Add the ocrs to the ocr collection
add_ocrs_to_collection(ocr_folder_path)