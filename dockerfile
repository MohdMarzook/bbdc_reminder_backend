FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    tesseract-ocr -y
COPY req.txt .
RUN pip install --no-cache-dir -r req.txt
COPY . .

EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
#  uvicorn main:app --host 0.0.0.0 --port 8000