FROM python:3.12-slim

WORKDIR /app

# System deps (psycopg2, pdf tools, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source (INCLUDING app/.env)
COPY . .

# Make Python output unbuffered
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
