FROM python:3.12

WORKDIR /python-code
COPY python/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY python/ .

EXPOSE 5000

CMD ["python", "server.py"]