from flask import Blueprint, render_template, redirect, session, request, flash, url_for
from flask_mail import Message
from decorators import login_required
from config import mysql, mail
from werkzeug.utils import secure_filename
import os, random, string

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def execute_query(query, *args):
    with mysql.connection.cursor() as cur:
        cur.execute(query, args)
        return cur.fetchall()

@admin_bp.route('/')
@login_required
def admin_index():
    return render_template('admin/index.html')

@admin_bp.route('/login')
def admin_login():
    return render_template('admin/login.html')

@admin_bp.route('/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@admin_bp.route('/login', methods=['POST'])
def admin_login_post():
    try:
        username = request.form['txtUsuario']
        password = request.form['txtPassword']
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM login WHERE username = %s AND password = %s", (username, password))
            login = cur.fetchone()
        
        if login is not None:
            if login[5] == 0:  
                session['login'] = True
                session['username'] = login[1]
                session['id_rol'] = login[4]
                session['id'] = login[0]

                if session['id_rol'] in {0, 1, 2}:  
                    return redirect('/admin')
                else:
                    return render_template('admin/login.html', mensaje='Access Denied: User not created.')
            else:
                return render_template('admin/login.html', mensaje='Waiting for confirmation.')
        else:
            return render_template('admin/login.html', mensaje='Access Denied, please verify your credentials.')
    except Exception as e:
        flash('Error fetching data from database', 'error')
        print(f"Error fetching data from database: {e}")
        return redirect('/admin/login')
    
@admin_bp.route('/registro', methods=['GET', 'POST'])
def admin_registro():
    if request.method == 'POST':
        # Formulario de registro
        username = request.form['txtUsuario']
        password = request.form['txtPassword']
        email = request.form['txtEmail']

        # Verificar si el nombre de usuario ya existe en la Base de Datos
        with mysql.connection.cursor() as cur:
            query = "SELECT id FROM login WHERE username = %s"
            cur.execute(query, (username,))
            existing_user = cur.fetchone()

            if existing_user:  # Usuario ya existe en la base de datos, salta error y cierra la conexion
                return render_template('admin/registro.html', error='USERNAME not valid')

        # Guardar los datos en la base de datos
        with mysql.connection.cursor() as cur:
            query = "INSERT INTO login (username, password, email, registro_pendiente) VALUES (%s, %s, %s, %s)"
            cur.execute(query, (username, password, email, 1))
        mysql.connection.commit()

        return redirect('/admin/login')  # Registro OK Redirigir al inicio 

    return render_template('admin/registro.html')



# Token para restablecer la contraseña
def generate_reset_token():
    token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
    return token

# Modifica la función de envío de correo para aceptar argumentos
def enviar_correo(destinatario, asunto, contenido):
    msg = Message(asunto, sender='karoltfg2023@gmail.com', recipients=[destinatario])
    msg.body = contenido

    # Intentar enviar el correo
    try:
        mail.send(msg)
        return True, None  # Correo enviado correctamente
    except Exception as e:
        # Manejar cualquier tipo de error que pueda ocurrir al enviarse el correo
        return False, str(e)

# olvide_contrasena, llama a enviar_correo
@admin_bp.route('/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        token = generate_reset_token()  # Genera un token para restablecer la contraseña

        # Guardar el token en la base de datos
        try:
            with mysql.connection.cursor() as cur:
                cur.execute("INSERT INTO reset_tokens (email, token) VALUES (%s, %s)", (email, token))
                mysql.connection.commit()

            # Intentar enviar el correo electrónico
            exito, error = enviar_correo(email, 'Password Reset', f'Click on the link to reset your password: {url_for("admin.restablecer_contrasena", token=token, _external=True)}')

            if exito:
                mensaje = "An email with instructions to reset your password has been sent."
                return render_template('admin/login.html', mensaje=mensaje)
            else:
                mensaje = f"An error occurred while sending the email. Please try again later. Error: {error}"
                return render_template('admin/olvide_contrasena.html', mensaje=mensaje)

        except Exception as e:
            flash('Error connecting to the database.', 'error')
            print(f"Database error: {e}")

    return render_template('admin/olvide_contrasena.html')

# Restablecer la contraseña
@admin_bp.route('/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']

        # Verificar el token en la base de datos
        try:
            with mysql.connection.cursor() as cur:
                cur.execute("SELECT email FROM reset_tokens WHERE token = %s", (token,))
                resultado = cur.fetchone()

                if resultado:
                    # Actualizar la contraseña en la base de datos
                    cur.execute("UPDATE login SET password = %s WHERE email = %s", (nueva_contrasena, resultado[0]))
                    mysql.connection.commit()

                    # Eliminar el token de la base de datos después de usarlo
                    cur.execute("DELETE FROM reset_tokens WHERE token = %s", (token))
                    mysql.connection.commit()

                    mensaje = "Password reset successful. You can now log in with your new password."
                    return render_template('admin/login.html', mensaje=mensaje)
                else:
                    mensaje = "The token is not valid. Please request another password reset."
                    return render_template('admin/login.html', mensaje=mensaje)

        except Exception as e:
            flash('Error connecting to the database.', 'error')
            print(f"Database error: {e}")

    return render_template('admin/restablecer_contrasena.html', token=token)

@admin_bp.route('/calendar')
@login_required
def admin_calendar():
    try:
        id_rol = session.get('id_rol', 0)  

        if id_rol == 0:
            tiene_permiso = False
        elif id_rol == 1 or id_rol == 2:
            tiene_permiso = True
        else:
            tiene_permiso = False

        calendar_query = "SELECT id, title, place, start_event, end_event FROM events"
        calendar = [
            {
                'id': event[0],
                'title': event[1],
                'place': event[2],
                'start': event[3].strftime('%Y-%m-%dT%H:%M:%S'),
                'end': event[4].strftime('%Y-%m-%dT%H:%M:%S')
            }
            for event in execute_query(calendar_query)
        ]

        return render_template('admin/calendar.html', calendar=calendar, tiene_permiso=tiene_permiso)

    except Exception as e:
        flash('Error fetching data from database', 'error')
        print(f"Error fetching data from database: {e}")
        return render_template('admin/calendar.html', calendar=[])
    

@admin_bp.route('/books')
@login_required
def admin_books():
    if 'login' not in session:
        return redirect('/admin/login')

    try:
       id_usuario_actual = session.get('id')
       id_rol = session.get('id_rol')
       if id_rol == 1 or id_rol == 2:
           libros_query = "SELECT * FROM `libros`"
       else:
           libros_query = "SELECT * FROM `libros` WHERE id_usuario = %s"


       autores_query = "SELECT id, nombre, apellido FROM autores"

       libros = execute_query(libros_query) if id_rol == 1 or id_rol == 2  else execute_query(libros_query, id_usuario_actual)
       autores_data = execute_query(autores_query)

       for libro in libros: 
            libro_id = libro[0]
            autor_id_libro = libro[6]
            autor_encontrado = False

            for autor_data in autores_data: 
                autor_id_data = autor_data[0]
                if autor_id_libro == autor_id_data:
                    autor_encontrado = True
                    break

            if not autor_encontrado: 
                mensaje_error = f"Author not found for book ID: {libro_id}"
                return render_template('admin/books.html', libros=libros, autores=autores_data, mensaje_error=mensaje_error)

       return render_template('admin/books.html', libros=libros, autores=autores_data) 

    except Exception as e:
        flash('Error fetching data from database', 'error')
        print(f"Error fetching data from database: {e}")
        return render_template('admin/books.html', libros=[], autores=[])


def guardar_archivo(archivo, carpeta_destino):
    if archivo.filename == '':
        return None  
    
    extension_permitida = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4']
    if '.' not in archivo.filename or archivo.filename.rsplit('.', 1)[1].lower() not in extension_permitida:        return None  
    
    nombre_archivo = secure_filename(archivo.filename)
    ruta_guardado = os.path.join(carpeta_destino, nombre_archivo)
    print("Intentando guardar archivo en:", ruta_guardado)
    archivo.save(ruta_guardado)
    
    return nombre_archivo

@admin_bp.route('/books/guardar', methods=['POST'])
def admin_libros_guardar():
    mensaje_error = None
    if not 'login' in session:
        return redirect('/admin/login')

    _nombre = request.form['txtNombre'].upper()
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']
    _year = request.form['txtYear']
    _area_seleccionada = request.form['txtArea']
    _autor_nombre = request.form['txtAutorNombre'].upper()
    _autor_apellido = request.form['txtAutorApellido'].upper()
    _descripcion = request.form['txtDescripcion']
    _video = request.files['txtVideo']
    _pdf = request.files['txtPDF']
    _imagen_secundaria = request.files['txtImagenSecundaria']
    id_usuario_actual = session.get('id')

    _archivo = guardar_archivo(request.files['txtImagen'], 'static/archivos/imagenes/')
    _video = guardar_archivo(request.files['txtVideo'], 'static/archivos/videos/')
    _pdf = guardar_archivo(request.files['txtPDF'], 'static/archivos/pdf/')
    _imagen_secundaria = guardar_archivo(request.files['txtImagenSecundaria'], 'static/archivos/imagenes/')

    # Verificar si algún campo está vacío
    if not _nombre or not _url or not _archivo or not _autor_nombre or not _autor_apellido:
        mensaje_error = 'Please fill in all the fields.'
        return render_template('admin/books.html', mensaje_error=mensaje_error)

    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT id FROM autores WHERE nombre = %s AND apellido = %s", (_autor_nombre, _autor_apellido))
            autor_existente = cur.fetchone()
            
            if autor_existente:
                _autor_id = autor_existente[0]  # Utilizar el ID del autor existente
            else:
                cur.execute("INSERT INTO autores (nombre, apellido) VALUES (%s, %s)", (_autor_nombre, _autor_apellido))
                mysql.connection.commit()
                _autor_id = cur.lastrowid  # Obtener el ID del nuevo autor

        with mysql.connection.cursor() as cur:
            cur.execute("SELECT id FROM areas WHERE nombre = %s", (_area_seleccionada,))
            resultado_area = cur.fetchone()
            
            if resultado_area:
                _area_id = resultado_area[0]  
            else:
                mensaje_error = 'Invalid area selected.'
                return render_template('admin/books.html', mensaje_error=mensaje_error)
        sql = "INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`, `year`, `area_id`, `autor_id`, `descripcion`, `video`, `pdf`, `imagen_secundaria`, `id_usuario`) VALUES (NULL, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s);"
        datos = (_nombre, _archivo, _url, _year, _area_id, _autor_id,_descripcion, _video, _pdf, _imagen_secundaria, id_usuario_actual)
        
        with mysql.connection.cursor() as cur:
            cur.execute(sql, datos)
            mysql.connection.commit()

        return redirect('/admin/books')

    except Exception as e:
        print(f"Error during database operation: {e}")
        mensaje_error = 'Error performing database operation.'
        return render_template('admin/books.html', mensaje_error=mensaje_error)

@admin_bp.route('/books/delete', methods=['POST'])
def admin_books_delete():
    # Check for authorization
    if 'login' not in session:
        return redirect('/admin/login')
    book_id = request.form['txtID']

    try:
        with mysql.connection.cursor() as cur:
            cur.execute("START TRANSACTION")
            cur.execute("DELETE FROM comentarios WHERE libro_id = %s", (book_id,))
            cur.execute("DELETE FROM libros WHERE id = %s", (book_id,))
            cur.execute("COMMIT")

        return redirect('/admin/books')

    except Exception as e:
        cur.execute("ROLLBACK")
        flash('Error deleting book.', 'error')
        print(f"Error deleting book: {e}")
        return redirect('/admin/books')


@admin_bp.route('/permisos', methods=['GET', 'POST'])
def admin_permisos():
    if request.method == 'POST':
        username = request.form['txtUsuario']
        password = request.form['txtPassword']
        email = request.form['txtEmail']
        id_rol = request.form['txtIdRol']
        registro_pendiente = request.form['registro_pendiente']

        # Guardar los datos en la base de datos
        with mysql.connection.cursor() as cur:
            query = "INSERT INTO login (username, password, email, id_rol, registro_pendiente) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (username, password, email, id_rol, registro_pendiente))
        mysql.connection.commit()

    # Verificar el acceso basado en el username
    if 'id_rol' in session and session['id_rol'] == 1:
        # Obtener todos los datos de la tabla de permisos
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM login")
            permisos = cur.fetchall()

        return render_template('admin/permisos.html', permisos=permisos)

    # Redirigir a la página anterior si no se cumple el requisito
    return redirect(request.referrer or '/')

@admin_bp.route('/permisos/editar', methods=['POST'])
def admin_permisos_editar():
    if not 'login' in session:
        return redirect('/admin/login')

    username = request.form['username']
    password = request.form['password']
    id_rol = request.form['id_rol']
    registro_pendiente = request.form['registro_pendiente']

    # Actualizar los campos en la base de datos
    with mysql.connection.cursor() as cur:
        query = "UPDATE login SET password = %s, id_rol = %s, registro_pendiente = %s WHERE username = %s"
        cur.execute(query, (password, id_rol, registro_pendiente, username))
    mysql.connection.commit()

    return redirect('/admin/permisos')

@admin_bp.route('/permisos/eliminar/<int:id_permiso>', methods=['GET'])
def admin_permisos_eliminar(id_permiso):
    if not 'login' in session:
        return redirect('/admin/login')

    # Eliminar el permiso de la base de datos
    with mysql.connection.cursor() as cur:
        query = "DELETE FROM login WHERE id = %s"
        cur.execute(query, (id_permiso,))
    mysql.connection.commit()

    return redirect('/admin/permisos')

@admin_bp.route('/permisos/aceptar/<int:id_permiso>', methods=['POST'])
def admin_permisos_aceptar(id_permiso):
    if not 'login' in session:
        return redirect('/admin/login')

    # Actualizar el valor de registro_pendiente a 0 en la base de datos
    with mysql.connection.cursor() as cur:
        query = "UPDATE login SET registro_pendiente = 0 WHERE id = %s"
        cur.execute(query, (id_permiso,))
    mysql.connection.commit()

    return redirect('/admin/permisos')

@admin_bp.route('/books/<int:libro_id>/comentarios', methods=['POST'])
def agregar_comentario(libro_id):
    try:
        print("Recibida solicitud POST para agregar comentario.")
        comentario = request.form['comentario']
        user_id = session.get('id')  
        print("Comentario:", comentario)
        print("User ID:", user_id)
        if user_id is None:
            return render_template('error.html', error_message='Debes iniciar sesión para comentar', back_url=request.referrer or '/')
        
        with mysql.connection.cursor() as cur:
            cur.execute("INSERT INTO comentarios (libro_id, comentario, user_id) VALUES (%s, %s, %s)", (libro_id, comentario, user_id))
            mysql.connection.commit()
        return redirect('/admin/books/' + str(libro_id))

    except Exception as e:
        print(f"Error en agregar_comentario: {e}")
        return render_template('error.html', error_message='Error al agregar comentario', back_url=request.referrer or '/')


@admin_bp.route('/books/comentarios/<int:comentario_id>/eliminar', methods=['POST', 'DELETE'])
def eliminar_comentario(comentario_id):
    user_id = session.get('id')
    if user_id is None:
        return render_template('error.html', error_message='Debes iniciar sesión para eliminar comentarios', back_url=request.referrer or '/')
    if request.method in ['POST', 'DELETE']:
        try:
            with mysql.connection.cursor() as cur:
                cur.execute("DELETE FROM comentarios WHERE id = %s", (comentario_id,))
                mysql.connection.commit()
            return redirect(request.referrer)
        except Exception as e:
            print("Error al eliminar comentario:", e)
            return render_template('error.html', error_message='Error al eliminar comentario', back_url=request.referrer or '/')
        
@admin_bp.route('/books/<int:libro_id>/editar', methods=['GET'])
def editar_libro(libro_id):
    if 'login' not in session:
        return redirect('/admin/login')

    with mysql.connection.cursor() as cur:
        cur.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
        libro = cur.fetchone()

        if libro:
            autor_id = libro[6]
            cur.execute("SELECT nombre, apellido FROM autores WHERE id = %s", (autor_id,))
            autor = cur.fetchone()
        else:
            autor = None

        cur.execute("SELECT * FROM areas")
        areas_data = cur.fetchall()

    if not libro:
        return render_template('error.html', error_message='Libro no encontrado')

    return render_template('admin/editar_libro.html', libro=libro, autor=autor, areas_data=areas_data)


@admin_bp.route('/books/<int:libro_id>/guardar', methods=['POST'])
def guardar_cambios_libro(libro_id):
    if 'login' not in session:
        return redirect('/admin/login')

    # Obtener los datos existentes del libro para comparar con los datos del formulario
    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
        libro_existente = cursor.fetchone()

    _nombre = request.form['txtNombre'].upper()
    _url = request.form['txtURL']
    _year = request.form['txtYear']
    _area_seleccionada = request.form['txtArea']
    _autor_nombre = request.form['txtAutorNombre'].upper()
    _autor_apellido = request.form['txtAutorApellido'].upper()
    _descripcion = request.form['txtDescripcion']
    _archivo = request.files['txtImagen'] if 'txtImagen' in request.files else None
    _video = request.files['txtVideo'] if 'txtVideo' in request.files else None
    _pdf = request.files['txtPDF'] if 'txtPDF' in request.files else None
    _imagen_secundaria = request.files['txtImagenSecundaria'] if 'txtImagenSecundaria' in request.files else None

    # Inicializar variables para guardar rutas de archivos
    archivo_path = None
    video_path = None
    pdf_path = None
    imagen_secundaria_path = None

    # Verificar si se deben eliminar los archivos
    eliminar_archivo = request.form.get('eliminarImagen')
    eliminar_video = request.form.get('eliminarVideo')
    eliminar_pdf = request.form.get('eliminarPDF')
    eliminar_imagen_secundaria = request.form.get('eliminarImagenSecundaria')

    # Actualizar la consulta SQL y los datos según sea necesario
    sql = "UPDATE libros SET nombre=%s, url=%s, year=%s, descripcion=%s"
    datos = (_nombre, _url, _year, _descripcion)

    if _archivo:
        archivo_path = guardar_archivo(_archivo, 'static/archivos/imagenes/')
        sql += ", imagen=%s"
        datos += (archivo_path,)
    elif eliminar_archivo:
        sql += ", imagen=NULL"

    if _area_seleccionada:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id FROM areas WHERE nombre = %s", (_area_seleccionada,))
            resultado_area = cursor.fetchone()
        if resultado_area:
            _area_id = resultado_area[0]  
            sql += ", area_id=%s"
            datos += (_area_id,)
        else:
            return redirect('/admin/libros', mensaje_error='Invalid area selected.')

    if _video:
        video_path = guardar_archivo(_video, 'static/archivos/videos/')
        sql += ", video=%s"
        datos += (video_path,)
    elif eliminar_video:
        sql += ", video=NULL"

    if _pdf:
        pdf_path = guardar_archivo(_pdf, 'static/archivos/pdf/')
        sql += ", pdf=%s"
        datos += (pdf_path,)
    elif eliminar_pdf:
        sql += ", pdf=NULL"

    if _imagen_secundaria:
        imagen_secundaria_path = guardar_archivo(_imagen_secundaria, 'static/archivos/imagenes/')
        sql += ", imagen_secundaria=%s"
        datos += (imagen_secundaria_path,)
    elif eliminar_imagen_secundaria:
        sql += ", imagen_secundaria=NULL"

    # Obtener el ID del autor si ya existe en la base de datos
    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT id FROM autores WHERE nombre = %s AND apellido = %s", (_autor_nombre, _autor_apellido))
        resultado_autor = cursor.fetchone()
    if resultado_autor:
        _autor_id = resultado_autor[0]  # Obtener el ID del autor
    else:
        # Si el autor no se encuentra en la base de datos, añadirlo
        with mysql.connection.cursor() as cursor:
            cursor.execute("INSERT INTO autores (nombre, apellido) VALUES (%s, %s)", (_autor_nombre, _autor_apellido))
            mysql.connection.commit()
            # Obtener el ID del autor recién añadido
            _autor_id = cursor.lastrowid

    # Ejecutar la consulta SQL con los datos actualizados
    sql += ", autor_id=%s WHERE id=%s"
    datos += (_autor_id, libro_id)
    with mysql.connection.cursor() as cursor:
        cursor.execute(sql, datos)
        mysql.connection.commit()

    return redirect('/admin/books')

@admin_bp.route('/links')
@login_required
def admin_links():
    if 'login' not in session:
        return redirect('/admin/login')

    try:
        id_usuario_actual = session.get('id')
        id_rol = session.get('id_rol')
        if id_rol == 1 or id_rol == 2:
            links_query = "SELECT * FROM links"
        else:
            links_query = "SELECT * FROM links WHERE user_id = %s"

        links = execute_query(links_query) if id_rol == 1 or id_rol == 2 else execute_query(links_query, id_usuario_actual)
        print(links)
        return render_template('admin/links.html', links=links)

    except Exception as e:
        flash('Error fetching data from database', 'error')
        print(f"Error fetching data from database: {e}")
        return render_template('admin/links.html', links=[])


@admin_bp.route('/links/guardar', methods=['POST'])
def admin_links_guardar():
    if not 'login' in session:
        return redirect('/admin/login')

    _nombre = request.form['nombre']
    _url = request.form['url']
    id_usuario_actual = session.get('id')

    # Verificar si algún campo está vacío
    if not _nombre or not _url:
        mensaje_error = 'Por favor, complete todos los campos.'
        return render_template('admin/links.html', mensaje_error=mensaje_error)

    try:
        with mysql.connection.cursor() as cur:
            sql = "INSERT INTO links (nombre, url, user_id) VALUES (%s, %s, %s)"
            cur.execute(sql, (_nombre, _url, id_usuario_actual))
            mysql.connection.commit()

        return redirect('/admin/links')

    except Exception as e:
        print(f"Error during database operation: {e}")
        mensaje_error = 'Error al realizar la operación en la base de datos.'
        return render_template('admin/links.html', mensaje_error=mensaje_error)


@admin_bp.route('/links/delete', methods=['POST'])
def admin_links_delete():
    if 'login' not in session:
        return redirect('/admin/login')

    link_id = request.form['link_id']

    try:
        with mysql.connection.cursor() as cur:
            cur.execute("DELETE FROM links WHERE id = %s", (link_id,))
            mysql.connection.commit()

        return redirect('/admin/links')

    except Exception as e:
        flash('Error deleting link.', 'error')
        print(f"Error deleting link: {e}")
        return redirect('/admin/links')

@admin_bp.route('/journals')
@login_required
def admin_journals():
    if 'login' not in session:
        return redirect('/admin/login')

    try:
        id_usuario_actual = session.get('id')
        id_rol = session.get('id_rol')
        if id_rol == 1 or id_rol == 2:
            journals_query = "SELECT * FROM journals"
        else:
            journals_query = "SELECT * FROM journals WHERE user_id = %s"

        journals = execute_query(journals_query) if id_rol == 1 or id_rol == 2 else execute_query(journals_query, id_usuario_actual)
        print(journals)
        return render_template('admin/journals.html', journals=journals)

    except Exception as e:
        flash('Error fetching data from database', 'error')
        print(f"Error fetching data from database: {e}")
        return render_template('admin/journals.html', journals=[])


@admin_bp.route('/journals/guardar', methods=['POST'])
def admin_journals_guardar():
    if not 'login' in session:
        return redirect('/admin/login')

    _title = request.form['title']
    _year = request.form['year']
    _link = request.form['link']
    _cover = request.files['cover']
    id_usuario_actual = session.get('id')

    # Guardar la imagen de portada
    _cover_filename = guardar_archivo(_cover, 'static/archivos/imagenes/')

    # Verificar si algún campo está vacío
    if not _title or not _year or not _link or not _cover_filename:
        mensaje_error = 'Por favor, complete todos los campos.'
        return render_template('admin/journals.html', mensaje_error=mensaje_error)

    try:
        with mysql.connection.cursor() as cur:
            sql = "INSERT INTO journals (title, year, link, cover, user_id) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(sql, (_title, _year, _link, _cover_filename, id_usuario_actual))
            mysql.connection.commit()

        return redirect('/admin/journals')

    except Exception as e:
        print(f"Error during database operation: {e}")
        mensaje_error = 'Error al realizar la operación en la base de datos.'
        return render_template('admin/journals.html', mensaje_error=mensaje_error)


@admin_bp.route('/journals/delete', methods=['POST'])
def admin_journals_delete():
    if 'login' not in session:
        return redirect('/admin/login')

    journal_id = request.form['journal_id']

    try:
        with mysql.connection.cursor() as cur:
            cur.execute("DELETE FROM journals WHERE id = %s", (journal_id,))
            mysql.connection.commit()

        return redirect('/admin/journals')

    except Exception as e:
        flash('Error deleting journal.', 'error')
        print(f"Error deleting journal: {e}")
        return redirect('/admin/journals')
