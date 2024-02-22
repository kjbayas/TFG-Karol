# sitio_routes.py
from flask import Blueprint, render_template, request
from decorators import login_required
from config import mysql

sitio_bp = Blueprint('sitio', __name__, url_prefix='/sitio')

# Ruta para mostrar la lista de libros
@sitio_bp.route('/books')
def books():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM `libros`")
            libros = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        libros = []
    return render_template('sitio/books.html', libros=libros)

@sitio_bp.route('/busqueda', methods=['GET'])
def buscar_libros():
    year = request.args.get('year')
    area = request.args.get('area')
    author = request.args.get('author')
    print("Year:", year)
    print("Area:", area)
    print("Author:", author)

    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id, nombre, apellido FROM autores")
            autores = cursor.fetchall()

            sql = "SELECT * FROM libros WHERE 1=1"
            conditions = []
            params = []

            if author:
                author_id = author
                conditions.append("autor_id = %s")
                params.append(author_id)
            if year:
                conditions.append("year = %s")
                params.append(year)
            if area:
                conditions.append("area_id = (SELECT id FROM areas WHERE nombre = %s)")
                params.append(area)

            if conditions:
                sql += " AND " + " AND ".join(conditions)

            cursor.execute(sql, params)
            libros = cursor.fetchall()

    except Exception as e:
        print(f"Error querying database: {e}")
        autores = []
        libros = []

    return render_template('sitio/books.html', libros=libros, autores=autores)


# Ruta para mostrar la lista de eventos 
@sitio_bp.route('/calendar')
def calendar():
    tiene_permiso = False
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT id, title, place, str_to_date(start_event, '%Y-%m-%d %H:%i:%s'), str_to_date(end_event, '%Y-%m-%d %H:%i:%s') FROM events")
            calendar = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        calendar = []
    
    return render_template('sitio/calendar.html', calendar=calendar, tiene_permiso=tiene_permiso)


# Ruta para mostrar la lista de links
@sitio_bp.route('/links')
def links():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links")
            links = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        links = []
    return render_template('sitio/links.html', links=links)

""" Esta funcion está pensada para que se pueda ver detalles de los links por si quiere ampliar 
@sitio_bp.route('/links/<int:link_id>')
def link_detail(link_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM links WHERE id = %s", (link_id,))
            link = cursor.fetchone()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        link = None
    return render_template('sitio/link_detail.html', link=link) 
    
"""
# Ruta para mostrar la lista de revistas

@sitio_bp.route('/journals')
def journals():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM journals")
            journals = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        journals = []
    return render_template('sitio/journals.html', journals=journals)
