from flask import Flask, flash, render_template, request, redirect, url_for, session, send_file
import csv
import io
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from functools import wraps
import logging
from config import Config
from utils import get_db_connection, close_db_connection, save_file, check_password

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar MySQL con la configuración explícita
app.config['MYSQL_HOST'] = Config.MYSQL_HOST
app.config['MYSQL_USER'] = Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = Config.MYSQL_DB
app.config['MYSQL_PORT'] = Config.MYSQL_PORT
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Verificar la conexión a la base de datos
with app.app_context():
    try:
        conexion, cursor = get_db_connection(mysql)
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()
        logger.info(f'Conexión exitosa a MySQL. Versión: {version}')
        close_db_connection(conexion, cursor)
    except Exception as e:
        logger.error(f'Error al conectar a la base de datos: {str(e)}')
        logger.error('Asegúrate de que MySQL está corriendo y las credenciales son correctas')

# Definición de roles
ROLES = {
    '1': 'administrativo',
    '2': 'tecnicos',
    '3': 'operativo'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión primero')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if session.get('user_role') != role:
                flash('No tienes permiso para acceder a esta página')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conexion = None
    cursor = None
    try:
        conexion, cursor = get_db_connection(mysql)
        
        # Primero verificamos si la tabla existe
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'capired'
            AND table_name = 'recurso_operativo'
        """)
        
        if cursor.fetchone()['COUNT(*)'] == 0:
            logger.error("La tabla recurso_operativo no existe en la base de datos")
            flash('Error: La tabla de recursos no está disponible')
            return render_template('dashboard.html', 
                                recurso_operativo=[],
                                user_role=session.get('user_role'))

        # Verificamos la estructura de la tabla
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = 'capired'
            AND table_name = 'recurso_operativo'
        """)
        
        columns = [column['COLUMN_NAME'] for column in cursor.fetchall()]
        required_columns = [
            'id_codigo_consumidor',
            'recurso_operativo_nombre',
            'recurso_operativo_cedula',
            'recurso_operativo_estado',
            'recurso_operativo_cargo'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            logger.error(f"Faltan columnas requeridas: {', '.join(missing_columns)}")
            flash('Error: La estructura de la tabla no es correcta')
            return render_template('dashboard.html', 
                                recurso_operativo=[],
                                user_role=session.get('user_role'))

        # Si todo está bien, realizamos la consulta principal
        sql = """
            SELECT 
                id_codigo_consumidor,
                recurso_operativo_nombre,
                recurso_operativo_cedula,
                COALESCE(recurso_operativo_estado, 'No definido') as recurso_operativo_estado,
                COALESCE(recurso_operativo_cargo, 'No definido') as recurso_operativo_cargo
            FROM capired.recurso_operativo
            ORDER BY recurso_operativo_nombre ASC
        """
        cursor.execute(sql)
        recurso_operativo = cursor.fetchall()
        
        if not recurso_operativo:
            logger.warning("No se encontraron recursos operativos en la base de datos")
            flash('No hay recursos operativos registrados')
            return render_template('dashboard.html', 
                                recurso_operativo=[],
                                user_role=session.get('user_role'))
        
        logger.debug(f"Se encontraron {len(recurso_operativo)} recursos operativos")
        return render_template('dashboard.html', 
                             recurso_operativo=recurso_operativo,
                             user_role=session.get('user_role'))
                             
    except Exception as e:
        logger.error(f'Error al cargar el dashboard: {str(e)}')
        flash('Error al cargar los datos. Por favor, contacte al administrador.')
        return render_template('dashboard.html', 
                             recurso_operativo=[],
                             user_role=session.get('user_role'))
    finally:
        if conexion and cursor:
            close_db_connection(conexion, cursor)

@app.route('/buscar', methods=['POST'])
@login_required
def buscar():
    recurso_operativo = []
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        search_type = request.form.get('search_type')
        
        if not search_query or not search_type:
            flash('Por favor, complete los campos de búsqueda')
            return redirect(url_for('dashboard'))
        
        conexion = None
        cursor = None
        try:
            conexion, cursor = get_db_connection(mysql)
            
            if search_type == 'nombre':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE recurso_operativo_nombre LIKE %s", ('%' + search_query + '%',))
            elif search_type == 'cedula':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE recurso_operativo_cedula LIKE %s", ('%' + search_query + '%',))
            elif search_type == 'codigo':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE id_codigo_consumidor LIKE %s", ('%' + search_query + '%',))
            
            recurso_operativo = cursor.fetchall()
            
            if not recurso_operativo:
                flash('No se encontraron resultados')
        except Exception as e:
            logger.error(f'Error en la búsqueda: {e}')
            flash('Error al realizar la búsqueda')
        finally:
            if conexion and cursor:
                close_db_connection(conexion, cursor)
    
    return render_template('dashboard.html', 
                         recurso_operativo=recurso_operativo,
                         user_role=session.get('user_role'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor, complete todos los campos')
            return redirect(url_for('login'))
        
        conexion = None
        cursor = None
        try:
            conexion, cursor = get_db_connection(mysql)
            cursor.execute(
                """SELECT id_codigo_consumidor, id_roles, recurso_operativo_password, 
                          recurso_operativo_nombre 
                   FROM recurso_operativo 
                   WHERE recurso_operativo_cedula = %s""",
                (username,)
            )
            user = cursor.fetchone()
            
            if user and check_password(user['recurso_operativo_password'], password):
                session.clear()
                session.permanent = True
                session['user_id'] = user['id_codigo_consumidor']
                session['user_role'] = ROLES.get(str(user['id_roles']))
                session['user_name'] = user['recurso_operativo_nombre']
                flash(f'Bienvenido, {user["recurso_operativo_nombre"]}!')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos')
        except Exception as e:
            logger.error(f'Error en login: {e}')
            flash('Error al intentar iniciar sesión')
        finally:
            if conexion and cursor:
                close_db_connection(conexion, cursor)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente')
    return redirect(url_for('login'))

# contabilidad
@app.route('/contabilidad')
def index_contabilidad():
    return render_template('modulos/contabilidad/index.html')

# almacen
@app.route('/almacen')
def index_almacen():
    conexion = None
    cursor = None
    try:
        conexion, cursor = get_db_connection(mysql)
        cursor.execute("SELECT * FROM capired.recurso_operativo")
        recurso_operativo = cursor.fetchall()
        return render_template('modulos/almacen/index.html', recurso_operativo=recurso_operativo)
    except Exception as e:
        logger.error(f'Error al obtener los datos: {e}')
        flash('Error al obtener los datos')
        return redirect(url_for('index'))
    finally:
        if conexion is not None and cursor is not None:
            close_db_connection(conexion, cursor)

@app.route('/almacen/create')
def create_almacen():
    return render_template('modulos/almacen/create.html')

@app.route('/almacen/create/guardar', methods=['POST'])
def guardar_movil():
    if request.method == 'POST':
        conexion = None
        cursor = None
        try:
            # Validar datos requeridos
            required_fields = ['id', 'nombre', 'cedula']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'El campo {field} es obligatorio')
                    return redirect(url_for('create_almacen'))

            # Procesar la foto
            foto_path = None
            if 'foto' in request.files:
                foto_path = save_file(request.files['foto'])

            # Preparar datos
            datos = (
                request.form['id'],
                request.form['nombre'],
                request.form['cedula'],
                request.form.get('carpeta'),
                request.form.get('estado'),
                request.form.get('cargo'),
                request.form.get('ciudad'),
                request.form.get('empresa'),
                request.form.get('cliente'),
                request.form.get('mail'),
                request.form.get('telefono'),
                foto_path
            )

            # Ejecutar la consulta
            conexion, cursor = get_db_connection(mysql)
            sql = """
                INSERT INTO capired.recurso_operativo (
                    id_codigo_consumidor, recurso_operativo_nombre, 
                    recurso_operativo_cedula, recurso_operativo_carpeta,
                    recurso_operativo_estado, recurso_operativo_cargo,
                    recurso_operativo_ciudad, recurso_operativo_empresa,
                    recurso_operativo_cliente, recurso_operativo_mail,
                    recurso_operativo_telefono, recurso_operativo_foto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, datos)
            conexion.commit()
            flash('Registro guardado exitosamente')

        except Exception as e:
            logger.error(f'Error al guardar los datos: {e}')
            flash('Error al guardar los datos')
            if conexion:
                conexion.rollback()
        finally:
            if conexion is not None and cursor is not None:
                close_db_connection(conexion, cursor)

        return redirect('/almacen')

@app.route('/almacen/Editar/<int:id_codigo_consumidor>')
def editar_almacen(id_codigo_consumidor):
    conexion, cursor = get_db_connection(mysql)
    try:
        cursor.execute("SELECT * FROM capired.recurso_operativo WHERE id_codigo_consumidor = %s", (id_codigo_consumidor,))
        recurso_operativo = cursor.fetchone()
        close_db_connection(conexion, cursor)
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_almacen'))
    return render_template('/modulos/almacen/edit.html', recurso_operativo=recurso_operativo)

@app.route('/almacen/edit/Actualizar', methods=['POST'])
def editar_movil():
    if request.method == 'POST':
        id_codigo = request.form['id']
        nombre = request.form['nombre']
        cedula = request.form['cedula']
        carpeta = request.form['carpeta']
        estado = request.form['estado']
        cargo = request.form['cargo']
        ciudad = request.form['ciudad']
        empresa = request.form['empresa']
        cliente = request.form['cliente']
        correo = request.form['mail']
        telefono = request.form['telefono']
        
        # Manejar la carga de la foto
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_path = filename
            else:
                foto_path = request.form['current_foto']
        else:
            foto_path = request.form['current_foto']

        sql = "UPDATE capired.recurso_operativo SET recurso_operativo_nombre = %s, recurso_operativo_cedula = %s, recurso_operativo_carpeta = %s, recurso_operativo_estado = %s, recurso_operativo_cargo = %s, recurso_operativo_ciudad = %s, recurso_operativo_empresa = %s, recurso_operativo_cliente = %s, recurso_operativo_mail = %s, recurso_operativo_telefono = %s, recurso_operativo_foto = %s WHERE id_codigo_consumidor = %s"
        conexion, cursor = get_db_connection(mysql)
        datos = (nombre, cedula, carpeta, estado, cargo, ciudad, empresa, cliente, correo, telefono, foto_path, id_codigo)
        cursor.execute(sql, datos)
        close_db_connection(conexion, cursor)
        return redirect('/almacen')

@app.route('/almacen/Eliminar/<int:id_codigo_consumidor>')
def eliminar_almacen(id_codigo_consumidor):
    conexion, cursor = get_db_connection(mysql)
    try:
        cursor.execute("DELETE FROM capired.recurso_operativo WHERE id_codigo_consumidor = %s", (id_codigo_consumidor,))
        conexion.commit()
    except Exception as e:
        flash(f'Error al eliminar los datos: {e}')
    finally:
        close_db_connection(conexion, cursor)
    return redirect('/almacen')

# logistica
@app.route('/logistica')
def index_logistica():
    return render_template('modulos/logistica/index.html')

# Modulo de Automotor
@app.route('/logistica/automotor')
def index_automotor():
    return render_template('modulos/logistica/automotor/index.html')

# Modulo de Dotaciones
@app.route('/logistica/dotaciones')
def index_dotaciones():
    return render_template('modulos/logistica/dotaciones/index.html')

# Modulo de Epps
@app.route('/logistica/epps')
def index_epps():
    return render_template('modulos/logistica/epps/index.html')

# Modulo de Herramientas
@app.route('/logistica/herramientas')
def index_herramientas():
    try:
        sql = "SELECT * FROM capired.asignacion a INNER JOIN capired.recurso_operativo c ON a.id_codigo_consumidor = c.id_codigo_consumidor;"
        conexion, cursor = get_db_connection(mysql)
        cursor.execute(sql)
        asignacion = cursor.fetchall()
        
        sql_tecnicos = "SELECT id_codigo_consumidor, recurso_operativo_nombre FROM capired.recurso_operativo ORDER BY recurso_operativo_nombre"
        cursor.execute(sql_tecnicos)
        lista_tecnico = cursor.fetchall()
        close_db_connection(conexion, cursor)
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_logistica'))
    
    return render_template('modulos/logistica/herramientas/index.html', asignacion=asignacion, lista_tecnico=lista_tecnico)

@app.route('/logistica/herramientas/create/guardar', methods=['POST'])
def guardar_herramientas():
    if request.method == 'POST':
        nombre = request.form['tecnico']
        fecha = request.form['fecha']
        estado = request.form.get('estado', 0)
        cargo = request.form['cargo']  
        adaptadorMandril = request.form.get('adaptadorMandril', 0)
        alicate = request.form.get('alicate', 0)
        barra45cm = request.form.get('asignacion_barra_45cm', 0)    
        cono_retractil = request.form.get('asignacion_cono_retractil', 0)    
        sql = "INSERT INTO capired.asignacion (id_codigo_consumidor, asignacion_fecha, asignacion_estado, asignacion_cargo, asignacion_adaptador_mandril, asignacion_alicate, asignacion_barra_45cm, asignacion_cono_retractil) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        conexion, cursor = get_db_connection(mysql)
        datos = (nombre, fecha, estado, cargo, adaptadorMandril, alicate, barra45cm, cono_retractil)
        cursor.execute(sql, datos)
        close_db_connection(conexion, cursor)
        return redirect('/logistica/herramientas')

@app.route('/logistica/herramientas/Eliminar/<int:id_asignacion>')
def eliminar_herramienta(id_asignacion):
    conexion, cursor = get_db_connection(mysql)
    try:
        cursor.execute("DELETE FROM capired.asignacion WHERE id_asignacion = %s", (id_asignacion,))
        conexion.commit()
    except Exception as e:
        flash(f'Error al eliminar los datos: {e}')
    finally:
        close_db_connection(conexion, cursor)
    return redirect('/logistica/herramientas')

@app.route('/logistica/herramientas/Editar/<int:id_asignacion>', methods=['GET', 'POST'])
def editar_herramienta(id_asignacion):
    conexion, cursor = get_db_connection(mysql)
    
    if request.method == 'POST':
        nombre = request.form['tecnico']
        fecha = request.form['fecha']
        estado = request.form.get('estado', 0)
        cargo = request.form['cargo']
        adaptadorMandril = request.form.get('adaptadorMandril', 0)
        alicate = request.form.get('alicate', 0)
        barra45cm = request.form.get('asignacion_barra_45cm', 0)
        cono_retractil = request.form.get('asignacion_cono_retractil', 0)
        observacion = request.form.get('observacion', '')

        sql = "UPDATE capired.asignacion SET id_codigo_consumidor = %s, asignacion_fecha = %s, asignacion_estado = %s, asignacion_cargo = %s, asignacion_adaptador_mandril = %s, asignacion_alicate = %s, asignacion_barra_45cm = %s, asignacion_cono_retractil = %s, observacion = %s WHERE id_asignacion = %s"
        datos = (nombre, fecha, estado, cargo, adaptadorMandril, alicate, barra45cm, cono_retractil, observacion, id_asignacion)
        
        try:
            cursor.execute(sql, datos)
            conexion.commit()
            flash('Datos actualizados correctamente')
        except Exception as e:
            flash(f'Error al actualizar los datos: {e}')
        finally:
            close_db_connection(conexion, cursor)
        return redirect('/logistica/herramientas')
    
    else:
        try:
            cursor.execute("SELECT * FROM capired.asignacion WHERE id_asignacion = %s", (id_asignacion,))
            asignacion = cursor.fetchone()
            
            sql_tecnicos = "SELECT id_codigo_consumidor, recurso_operativo_nombre FROM capired.recurso_operativo ORDER BY recurso_operativo_nombre"
            cursor.execute(sql_tecnicos)
            lista_tecnico = cursor.fetchall()
        except Exception as e:
            flash(f'Error al obtener los datos: {e}')
            return redirect(url_for('index_logistica'))
        finally:
            close_db_connection(conexion, cursor)
        
        return render_template('/modulos/logistica/herramientas/edit.html', asignacion=asignacion, lista_tecnico=lista_tecnico)

# Modulo de Inventario
@app.route('/logistica/inventario')
def index_inventario():
    return render_template('modulos/logistica/inventario/index.html')

# Modulo de Mobiliario
@app.route('/logistica/mobiliario')
def index_mobiliario():
    return render_template('modulos/logistica/mobiliario/index.html')

# Modulo de Reporte
@app.route('/logistica/reporte')
def index_reporte():
    return render_template('modulos/logistica/reporte/index.html')

# Modulo de Suministros
@app.route('/logistica/suministros')
def index_suministros():
    try:
        sql = "SELECT * FROM capired.suministros"
        conexion, cursor = get_db_connection(mysql)
        cursor.execute(sql)
        suministros = cursor.fetchall()
        close_db_connection(conexion, cursor)
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_logistica'))
    finally:
        close_db_connection(conexion, cursor)
    return render_template('modulos/logistica/suministros/index.html', suministros=suministros)

@app.route('/logistica/suministros/create')
def create_suministros():
    return render_template('modulos/logistica/suministros/create.html')

@app.route('/logistica/suministros/create/guardar', methods=['POST'])
def guardar_suministros():
    if request.method == 'POST':
        codigo = request.form['codigo']
        descripcion = request.form['descripcion']
        unidad_medida = request.form.get('unidad_medida', 0)
        familia = request.form['familia']
        cliente = request.form['cliente']
        requiere = request.form['requiere_serial']
        costo_unitario = request.form['costo_unitario']
        cantidad = request.form['cantidad']
        sql = "INSERT INTO capired.suministros (suministros_codigo, suministros_descripcion, suministros_unidad_medida, suministros_familia, suministros_cliente, suministros_requiere_serial, suministros_costo_unitario, suministros_cantidad) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"        
        conexion, cursor = get_db_connection(mysql)
        datos = (codigo, descripcion, unidad_medida, familia, cliente, requiere, costo_unitario, cantidad)
        cursor.execute(sql, datos)
        close_db_connection(conexion, cursor)
        return redirect('/logistica/suministros')

# Modulo de Administracion
@app.route('/administrativo')
@role_required('1')
def index_administrativo():
    return render_template('modulos/administrativo/index.html')

#Modulo Operativo
@app.route('/operativo')
@role_required('3')
def index_operativo():
    return render_template('modulos/operativo/index.html')

# Modulo de Tecnicos
@app.route('/tecnicos')
@role_required('2')
def index_tecnicos():
    return render_template('modulos/tecnicos/index.html')

@app.route('/almacen/exportar')
def exportar_csv():
    conexion = None
    cursor = None
    try:
        conexion, cursor = get_db_connection(mysql)
        cursor.execute("SELECT * FROM capired.recurso_operativo")
        datos = cursor.fetchall()
        
        if not datos:
            flash('No hay datos para exportar')
            return redirect(url_for('index_almacen'))
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=datos[0].keys())
        writer.writeheader()
        writer.writerows(datos)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='datos.csv'
        )
    except Exception as e:
        logger.error(f'Error al exportar los datos: {e}')
        flash('Error al exportar los datos')
        return redirect(url_for('index_almacen'))
    finally:
        if conexion is not None and cursor is not None:
            close_db_connection(conexion, cursor)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)