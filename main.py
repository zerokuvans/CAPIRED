from flask import Flask, flash, render_template, request, redirect, url_for, session, send_file
import csv
import io
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuración de la base de datos
MySQL = MySQL()
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT'))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
MySQL.init_app(app)


# Definición de roles
ROLES = {
    '1': 'administrativo',
    '2': 'tecnicos',
    '3': 'operativo'
}

# Decorador para la ruta de login
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] != role:
                flash('No tienes permiso para acceder a esta página.')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Por favor, inicia sesión primero')
        return redirect(url_for('login'))
    
    recurso_operativo = []
    if request.method == 'POST':
        search_query = request.form['search_query']
        search_type = request.form['search_type']
        
        conexion = MySQL.connection
        cursor = conexion.cursor()
        
        try:
            if search_type == 'nombre':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE recurso_operativo_nombre LIKE %s", ('%' + search_query + '%',))
            elif search_type == 'cedula':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE recurso_operativo_cedula LIKE %s", ('%' + search_query + '%',))
            elif search_type == 'codigo':
                cursor.execute("SELECT * FROM capired.recurso_operativo WHERE id_codigo_consumidor LIKE %s", ('%' + search_query + '%',))
            
            recurso_operativo = cursor.fetchall()
        except Exception as e:
            flash(f'Error al buscar los datos: {e}')
        finally:
            cursor.close()
            conexion.commit()
    
    return render_template('dashboard.html', recurso_operativo=recurso_operativo)

# contabilidad
@app.route('/contabilidad')
def index_contabilidad():
    return render_template('modulos/contabilidad/index.html')

# almacen
@app.route('/almacen')
def index_almacen():
    try:
        sql = "SELECT * FROM capired.recurso_operativo"
        conexion = MySQL.connection
        cursor = conexion.cursor()
        cursor.execute(sql)
        recurso_operativo = cursor.fetchall()
        conexion.commit()
        return render_template('modulos/almacen/index.html', recurso_operativo=recurso_operativo)
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index'))
    finally:
        cursor.close()

@app.route('/almacen/create')
def create_almacen():
    return render_template('modulos/almacen/create.html')

@app.route('/almacen/create/guardar', methods=['POST'])
def guardar_movil():
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
                foto_path = None
        else:
            foto_path = None

        if not id_codigo or not nombre or not cedula:
            flash('Todos los campos son obligatorios')
            return redirect(url_for('create_almacen'))

        sql = "INSERT INTO capired.recurso_operativo (id_codigo_consumidor, recurso_operativo_nombre, recurso_operativo_cedula, recurso_operativo_carpeta, recurso_operativo_estado, recurso_operativo_cargo, recurso_operativo_ciudad, recurso_operativo_empresa, recurso_operativo_cliente, recurso_operativo_mail, recurso_operativo_telefono, recurso_operativo_foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        conexion = MySQL.connection
        datos = (id_codigo, nombre, cedula, carpeta, estado, cargo, ciudad, empresa, cliente, correo, telefono, foto_path)
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, datos)
            conexion.commit()
        except Exception as e:
            flash(f'Error al guardar los datos: {e}')
        finally:
            cursor.close()
        return redirect('/almacen')

@app.route('/almacen/Editar/<int:id_codigo_consumidor>')
def editar_almacen(id_codigo_consumidor):
    conexion = MySQL.connection
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM capired.recurso_operativo WHERE id_codigo_consumidor = %s", (id_codigo_consumidor,))
        recurso_operativo = cursor.fetchone()
        conexion.commit()
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_almacen'))
    finally:
        cursor.close()
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
        conexion = MySQL.connection
        datos = (nombre, cedula, carpeta, estado, cargo, ciudad, empresa, cliente, correo, telefono, foto_path, id_codigo)
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, datos)
            conexion.commit()
        except Exception as e:
            flash(f'Error al actualizar los datos: {e}')
        finally:
            cursor.close()
        return redirect('/almacen')

@app.route('/almacen/Eliminar/<int:id_codigo_consumidor>')
def eliminar_almacen(id_codigo_consumidor):
    conexion = MySQL.connection
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM capired.recurso_operativo WHERE id_codigo_consumidor = %s", (id_codigo_consumidor,))
        conexion.commit()
    except Exception as e:
        flash(f'Error al eliminar los datos: {e}')
    finally:
        cursor.close()
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
        conexion = MySQL.connection
        cursor = conexion.cursor()
        cursor.execute(sql)
        asignacion = cursor.fetchall()
        
        sql_tecnicos = "SELECT id_codigo_consumidor, recurso_operativo_nombre FROM capired.recurso_operativo ORDER BY recurso_operativo_nombre"
        cursor.execute(sql_tecnicos)
        lista_tecnico = cursor.fetchall()
        conexion.commit()
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_logistica'))
    finally:
        cursor.close()
    
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
        conexion = MySQL.connection
        datos = (nombre, fecha, estado, cargo, adaptadorMandril, alicate, barra45cm, cono_retractil)
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, datos)
            conexion.commit()
        except Exception as e:
            flash(f'Error al guardar los datos: {e}')
        finally:
            cursor.close()
        return redirect('/logistica/herramientas')

@app.route('/logistica/herramientas/Eliminar/<int:id_asignacion>')
def eliminar_herramienta(id_asignacion):
    conexion = MySQL.connection
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM capired.asignacion WHERE id_asignacion = %s", (id_asignacion,))
        conexion.commit()
    except Exception as e:
        flash(f'Error al eliminar los datos: {e}')
    finally:
        cursor.close()
    return redirect('/logistica/herramientas')

@app.route('/logistica/herramientas/Editar/<int:id_asignacion>', methods=['GET', 'POST'])
def editar_herramienta(id_asignacion):
    conexion = MySQL.connection
    cursor = conexion.cursor()
    
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
            cursor.close()
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
            cursor.close()
        
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
        conexion = MySQL.connection
        cursor = conexion.cursor()
        cursor.execute(sql)
        suministros = cursor.fetchall()
        conexion.commit()
    except Exception as e:
        flash(f'Error al obtener los datos: {e}')
        return redirect(url_for('index_logistica'))
    finally:
        cursor.close()
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
        conexion = MySQL.connection
        datos = (codigo, descripcion, unidad_medida, familia, cliente, requiere, costo_unitario, cantidad)
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, datos)
            conexion.commit()
        except Exception as e:
            flash(f'Error al guardar los datos: {e}')
        finally:
            cursor.close()
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



# Modulo login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validar las credenciales del usuario
        sql = "SELECT id_codigo_consumidor, id_roles FROM recurso_operativo WHERE recurso_operativo_cedula = %s AND recurso_operativo_password = %s"
        conexion = MySQL.connection
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            
            if user:
                flash('Inicio de sesión exitoso')
                session['user_id'] = user['id_codigo_consumidor']
                session['user_role'] = ROLES.get(user['id_roles'])
                return redirect(url_for('dashboard'))
            else:
                flash('Nombre de usuario o contraseña incorrectos')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al validar las credenciales: {e}')
        finally:
            cursor.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Eliminar la sesión del usuario
    session.pop('user_id', None)
    flash('Has cerrado sesión exitosamente')
    return redirect(url_for('login'))

@app.route('/almacen/exportar')
def exportar_csv():
    try:
        # Realizar la consulta a la base de datos para obtener los datos
        sql = "SELECT * FROM capired.recurso_operativo"
        conexion = MySQL.connection
        cursor = conexion.cursor()
        cursor.execute(sql)
        datos = cursor.fetchall()
        
        # Crear el archivo CSV en memoria
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=datos[0].keys())
        writer.writeheader()
        writer.writerows(datos)
        output.seek(0)
        
        # Enviar el archivo CSV como respuesta
        return send_file(output, mimetype='text/csv', attachment_filename='datos.csv', as_attachment=True)
    except Exception as e:
        flash(f'Error al exportar los datos: {e}')
        return redirect(url_for('index_almacen'))
    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(debug=True)