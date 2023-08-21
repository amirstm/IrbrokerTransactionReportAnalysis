FROM python:3.9.17

WORKDIR /python-code
COPY python/ .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "test.py"]