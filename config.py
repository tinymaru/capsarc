# config.py
import os

class Config:
    UPLOAD_FOLDER = os.path.join('static', 'images')  # Upload folder for image files
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    
    @staticmethod
    # image files
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
 
