import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from app.main.settings import Config
from PIL import Image
import numpy as np

class ChromaDBService:
    def __init__(self):
        self.db_path = Config.CHROMA_DB_PATH
        self.embedding_function = OpenCLIPEmbeddingFunction()
        self.data_loader = ImageLoader()
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.visual_collection = self.client.get_or_create_collection(
            name='multimodal_collection',
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
        )


        self.caption_collection = self.client.get_or_create_collection(
            name='caption_collection',
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
        )

        self.ocr_collection = self.client.get_or_create_collection(
            name='ocr_collection',
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
        )

    def get_result(self, caption, top_k):
        results_visual = self.visual_collection.query(query_texts=[caption], n_results=top_k, include=['distances'])
        results_caption = self.caption_collection.query(query_texts=[caption], n_results=top_k, include=['distances'])

        return consolidate_results(results_visual, results_caption, top_k)
    
    def get_result_one_image_no_text(self, image_path, image_captions, top_k):
        # Open and process the image to convert it into an array
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)
        
        print('Image array shape:', img_array.shape)

        # Pass the image array to the query method
        results_visual = self.visual_collection.query(query_images=[img_array], n_results=top_k, include=['distances'])
        results_caption = self.caption_collection.query(query_texts=image_captions, n_results=top_k, include=['distances'])

        return consolidate_results(results_visual, results_caption, top_k)
    
def consolidate_results(results1, results2, top_k):
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
    return sorted_results[:top_k]
