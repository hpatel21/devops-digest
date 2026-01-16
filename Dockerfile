FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY devops-digest.py .
COPY reports/ ./reports/

ENTRYPOINT ["python", "devops-digest.py"]
