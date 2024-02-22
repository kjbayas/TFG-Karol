from flask import Flask, render_template, redirect, session, request, flash, jsonify
from flask_mysqldb import MySQL
from config import Config, mail
from decorators import login_required
from admin_routes import admin_bp
from sitio_routes import sitio_bp
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)
mail.init_app(app)


# Definir la configuración de sesión para mayor seguridad
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('sitio/index.html')

@app.route('/sitio/admin/books/<int:libro_id>', methods=['GET'])
@app.route('/admin/books/<int:libro_id>', methods=['GET'])
@app.route('/sitio/admin/books.html/<int:libro_id>', methods=['GET', 'POST'])
def ver_libro(libro_id):
    try:
        # Utilizando el bloque with para gestionar el cursor
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
            libro = cur.fetchone()

            if not libro:
                flash('Libro no encontrado', 'error')
                return render_template('error.html', error_message='Libro no encontrado')

            cur.execute("SELECT id, nombre, apellido FROM autores WHERE id = %s", (libro[6],))
            autores_data = cur.fetchall()

            cur.execute(
                "SELECT comentarios.id, comentarios.comentario, login.username, comentarios.user_id FROM comentarios INNER JOIN login ON comentarios.user_id = login.id WHERE comentarios.libro_id = %s",
                (libro_id,))
            comentarios = cur.fetchall()

        return render_template('detalle_libro.html', libro=libro, autores=autores_data, comentarios=comentarios)
    except Exception as e:
        flash(f'Error al obtener los detalles del libro: {e}', 'error')
        print(f'Error al obtener los detalles del libro: {e}')
        return render_template('error.html', error_message='Error al obtener los detalles del libro')
    

@app.route("/update", methods=["POST"])
def update_event():
    try:
        event_id = request.form.get('id')
        title = request.form.get('title')
        place = request.form.get('place')
        start = request.form.get('start')
        end = request.form.get('end')

        with mysql.connection.cursor() as cursor:
            cursor.execute("UPDATE events SET title=%s, place=%s, start_event=%s, end_event=%s WHERE id=%s",
                           (title, place, start, end, event_id))
            mysql.connection.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        flash(f'Error al actualizar el evento: {e}', 'error')
        print(f'Error al actualizar el evento: {e}')
        return jsonify({'status': 'error', 'message': f'Error: {e}'})

@app.route("/insert", methods=["POST"])
def insert_event():
    try:
        title = request.form.get('title')
        place = request.form.get('place')
        start_str = request.form.get('start')
        end_str = request.form.get('end')

        # Validar si las cadenas de fecha no están vacías
        if not title or not start_str or not end_str:
            raise ValueError('Todos los campos deben ser completados.')

        # Convertir las cadenas de fecha en objetos datetime
        start = datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%S')
        end = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%S')

        # Validar si la fecha y hora de inicio son anteriores a la de finalización
        if start >= end:
            raise ValueError('La fecha y hora de inicio debe ser anterior a la de finalización.')

        with mysql.connection.cursor() as cursor:
            cursor.execute("INSERT INTO events (title, place, start_event, end_event) VALUES (%s, %s, %s, %s)",
                           (title, place, start, end))
            mysql.connection.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        flash(f'Error al insertar el evento: {e}', 'error')
        print(f'Error al insertar el evento: {e}')
        return jsonify({'status': 'error', 'message': f'Error: {e}'})

@app.route("/ajax_delete", methods=["POST"])
def ajax_delete():
    try:
        if request.method == 'POST':
            getid = request.form['id']
            print(getid)

            with mysql.connection.cursor() as cursor:
                cursor.execute("DELETE FROM events WHERE id=%s", (getid,))
                mysql.connection.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f'Error al eliminar el evento: {e}')
        return jsonify({'status': 'error', 'message': f'Error: {e}'})

# Rutas de sitio y admin
app.register_blueprint(admin_bp)
app.register_blueprint(sitio_bp)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
