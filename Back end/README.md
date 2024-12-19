1. Set Virtual environment
Install all project dependencies using:
```
$ pip install -r requirements.txt
```
Could need to 'pip install Flask'

2. In folder "Back end", create file .env containing the line GEMINI_API_KEY="AIzaSyAJmgIA-h6gBBqeEdSy1fUro-9HzAgu_i8" (you can change the value of the key by your own)

3. Let the folder "dataset/" in folder "app/database/"

4. Creating folder named "Manga-Search-Engine images_received" in your disk D:/, so that the server could receive images uploaded by users.

5. Running
```
flask run --host=0.0.0.0
```