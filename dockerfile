FROM python:3.10-slim

# Instalează dependențele de sistem
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Setează directorul de lucru
WORKDIR /app

# Copiază fișierele de requirements
COPY requirements.txt .

# Instalează dependențele Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiază codul aplicației
COPY . .

# Creează directorul pentru fișierele temporare
RUN mkdir -p /tmp/audio

# Expune portul
EXPOSE 9000

# Comandă pentru a rula aplicația
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]