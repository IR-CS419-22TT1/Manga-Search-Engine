from flask_restful import Resource
from flask import send_from_directory, send_file
from app.services.upload_image_service import ImageService
import os
from werkzeug.utils import safe_join

UPLOAD_FOLDER = '/tmp'
GET_IMAGE_ROUTE = '/get-image/<string:filename>'

class GetImage(Resource):
    def __init__(self):
        self.image_service = ImageService(UPLOAD_FOLDER)

    def get(self, filename):
        if self.image_service.image_exists(filename):
            print(f'Image found: {filename}')
            path = safe_join(os.fspath(UPLOAD_FOLDER), os.fspath(filename))
            print(f'Path: {path}')
            return send_from_directory(UPLOAD_FOLDER, filename)
        else:
            return {'message': 'Image not found'}, 404
        

# For testing:
# curl http://localhost:5000/get-image/your-image.jpg --output your-image.jpg