import os
import logging
from werkzeug.utils import secure_filename
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
import MySQLdb

logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        return filename
    return None

def get_db_connection(mysql):
    """Obtener una conexión a la base de datos de manera segura"""
    conexion = None
    cursor = None
    try:
        # Verificar el contexto de la aplicación
        if not current_app:
            raise RuntimeError("Working outside of application context")
        
        # Logging de la información de conexión (sin contraseña)
        logger.debug(f"Intentando conectar a MySQL en {Config.MYSQL_HOST}:{Config.MYSQL_PORT} "
                    f"con usuario {Config.MYSQL_USER} a la base de datos {Config.MYSQL_DB}")
        
        # Intentar obtener la conexión
        try:
            conexion = mysql.connection
            if conexion is None:
                raise MySQLdb.Error("No se pudo establecer la conexión con MySQL")
        except Exception as e:
            logger.error(f"Error al obtener la conexión MySQL: {str(e)}")
            raise
            
        # Intentar crear el cursor
        try:
            cursor = conexion.cursor()
            if cursor is None:
                raise MySQLdb.Error("No se pudo crear el cursor de la base de datos")
        except Exception as e:
            logger.error(f"Error al crear el cursor: {str(e)}")
            if conexion:
                conexion.close()
            raise
        
        # Verificar la conexión
        try:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()
            logger.debug(f"Conexión exitosa a la base de datos: {db_name}")
        except Exception as e:
            logger.error(f"Error al verificar la base de datos: {str(e)}")
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
            raise
        
        return conexion, cursor
    except Exception as e:
        logger.error(f"Error detallado al conectar a la base de datos: {str(e)}")
        if conexion:
            conexion.close()
        raise

def close_db_connection(conexion, cursor):
    """Cerrar la conexión a la base de datos de manera segura"""
    try:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
        logger.debug("Conexión a la base de datos cerrada correctamente")
    except Exception as e:
        logger.error(f"Error al cerrar la conexión a la base de datos: {str(e)}")

def hash_password(password):
    """Genera un hash seguro de la contraseña"""
    return generate_password_hash(password)

def check_password(hashed_password, password):
    """Verifica si la contraseña coincide con el hash"""
    return check_password_hash(hashed_password, password) 