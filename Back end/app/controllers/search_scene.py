from flask_restful import Resource, reqparse
from app.services.search_scene_service import SearchSceneService

SEARCH_SCENE_ROUTE = '/search-scene'

class SearchScene(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('image_path', type=list[str], location='json', required=False, help='Image path is required')
        self.parser.add_argument('text', type=list[str], location='json', required=False, help='Text is required')
        self.parser.add_argument('top_k', type=int, location='json', required=True, help='Top k is required')
        self.service = SearchSceneService()
    # def get(self):
        # pass
    def post(self):
        args = self.parser.parse_args()
        image_path = args['image_path']
        top_k = args['top_k']
        text = args['text']
        
        print(len(image_path), image_path)
        print(len(text), text)
        
        # Handle case where text is a list containing an empty string
        if len(text) == 1 and text[0] == '':
            text = []
            if len(image_path) == 1:
                print('only one image no text')
                return self.service.get_result_one_image_no_text(image_path, text, top_k)

        if not text:
            text = []
        
        if not image_path:
            image_path = []
        
        print('text:', text)
        print('image_path:', image_path)
        return self.service.get_result(image_path, text, top_k)