import os

class DeleteUserService:
    def __init__(self, user_folder):
        self.user_folder = user_folder

    def delete_user(self, user_id):
        try:
            # Create the folder path
            user_path = os.path.join(self.user_folder, str(user_id))

            # Try to delete the folder
            try:
                os.rmdir(user_path)
                return "User folder deleted successfully"
            except FileNotFoundError:
                return "User folder not found"
        except Exception as e:
            # Log the error (optional) and return False in case of failure
            return f"Error deleting user folder: {e}"