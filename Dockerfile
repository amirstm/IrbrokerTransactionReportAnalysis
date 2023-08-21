FROM python:3.9.17

WORKDIR /python-code
COPY python/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY python/ .

CMD ["python", "test.py"]