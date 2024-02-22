# config.py
from flask_mysqldb import MySQL
from flask_mail import Mail


class Config:
    #MYSQL_HOST = '10.22.2.63'
    MYSQL_HOST ='192.168.1.14'
    #MYSQL_HOST = 'localhost'
    #MYSQL_HOST = '192.168.1.18'
    #MYSQL_HOST = '10.0.60.183'
    MYSQL_USER = 'karolbayas'
    MYSQL_PASSWORD = 'urjc2024'
    MYSQL_DB = 'sitio'

     # Configuración del servidor de correo
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'karoltfg2023@gmail.com'
    MAIL_PASSWORD = 'jumhosncwxjihlyx'

mysql = MySQL()
mail = Mail()


    

