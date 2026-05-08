FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir checkov==3.1.43
RUN pip install --no-cache-dir --force-reinstall openai==1.30.1

# Copy ALL backend files into /app
COPY . .

# Confirm app module is visible
RUN python -c "from app.main import app; print('Import OK')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]