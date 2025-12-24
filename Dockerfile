FROM python:3.12
COPY requirements.lock ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 

COPY . ./
CMD gunicorn -b 0.0.0.0:${PORT} app:server
