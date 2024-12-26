from flask_restful import Resource, reqparse
from app.services.delete_user_service import DeleteUserService
import os
from app.main.settings import Config

USER_FOLDER = os.path.abspath(os.path.join(Config.CHROMA_DB_PATH, 'user'))
DELETE_USER_ROUTE = '/delete-user'

class DeleteUser(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user_id', type=int, location='json', required=True, help='User ID is required')
        self.user_service = DeleteUserService(USER_FOLDER)
    
    def post(self):
        try:
            args = self.parser.parse_args()
            user_id = args['user_id']
            state = self.user_service.delete_user(user_id)
            return {'state': state}, 200
        except Exception as e:
            return {'error': str(e)}, 500