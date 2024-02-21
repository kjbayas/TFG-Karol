# docker build -t tfgkarol .
# docker run -p 8000:5000 tfgkarol
# http://localhost:8000 
# Docker account
#  karoltfg2023@gmail.com
# jumhosncwxjihlyx
FROM python:3.8

# Instala nano para la edición de archivos
RUN apt-get update && apt-get install -y nano

WORKDIR /app

COPY app.py /app
COPY config.py /app
COPY admin_routes.py /app
COPY sitio_routes.py /app
COPY decorators.py /app
COPY static /app/static
COPY templates /app/templates
COPY requirements.txt /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
