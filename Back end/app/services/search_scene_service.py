from app.services.chromadb_service import ChromaDBService
from app.services.gemini_service import GeminiService

class SearchSceneService():
    def __init__(self):
        self.chromadb_service = ChromaDBService()
        self.gemini_service = GeminiService()

    def format_result(self, result):
        results = []
        for id, distance in result:
            base_name = id.split('.')[0]
            fields = base_name.split('_')
            results.append({
                "id": f'{fields[1]}_{fields[2]}_{fields[3]}',
                "distance": distance,
                "manga": fields[1],
                "page_type": fields[2],
                "page_number": fields[3],
            })
        return {
            "results": results
        }
    
    def get_result(self, image_paths, text_inputs, top_k):
        image_captions = [self.gemini_service.generate_caption(image_path) for image_path in image_paths]
        combined_text = self.gemini_service.combine_text_inputs(text_inputs)
        combined_captions = self.gemini_service.combine_image_captions(image_captions)

        combined_text_and_captions = self.gemini_service.combine_text_image_caption(combined_text, combined_captions)

        # return self.chromadb_service.get_result(combined_text_and_captions, top_k)
        return self.format_result(self.chromadb_service.get_result(combined_text_and_captions, top_k))
    
    def get_result_one_image_no_text(self, image_path, text, top_k):
        image_captions = self.gemini_service.generate_caption(image_path[0])
        return self.format_result(self.chromadb_service.get_result_one_image_no_text(image_path[0], image_captions, top_k))




