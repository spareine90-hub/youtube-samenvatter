FROM python:3.9-slim

WORKDIR /app

# Kopieer eerst de lijst met benodigdheden
COPY requirements.txt .

# Installeer de bibliotheken in de container
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de code
COPY . .

CMD ["python", "backend.py"]