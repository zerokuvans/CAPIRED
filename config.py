from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

class Config:
    # Configuración básica
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configuración de MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '732137a031e4b')
    MYSQL_DB = os.getenv('MYSQL_DB', 'capired')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Configuraciones adicionales de MySQL para compatibilidad
    MYSQL_DATABASE_HOST = MYSQL_HOST
    MYSQL_DATABASE_PORT = MYSQL_PORT
    MYSQL_DATABASE_USER = MYSQL_USER
    MYSQL_DATABASE_PASSWORD = MYSQL_PASSWORD
    MYSQL_DATABASE_DB = MYSQL_DB
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configuración de la sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax' 