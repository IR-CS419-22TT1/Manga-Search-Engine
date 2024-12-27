from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage
from app.services.upload_image_service import ImageService
import os
from app.main.settings import Config

UPLOAD_FOLDER = os.path.abspath(os.path.join(Config.CHROMA_DB_PATH, 'images_upload'))
UPLOAD_IMAGE_ROUTE = '/upload-image'

class UploadImage(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('file', type=FileStorage, location='files', required=True, help='Image file is required')
        self.parser.add_argument('user_id', type=str, location='form', required=True, help='User ID is required')  # Updated 'json' to 'form'
        self.image_service = ImageService(UPLOAD_FOLDER)

    def post(self):
        args = self.parser.parse_args()
        image = args['file']
        user_id = args['user_id']

        if image:
            filepath = self.image_service.save_image(image, user_id)
            return {'message': 'Image uploaded successfully', 'image_path': filepath}, 201
        else:
            return {'message': 'No image provided'}, 400
        

# For testing:
# curl -X POST -F "image=@/path/to/your/image.jpg" http://localhost:5000/upload-image