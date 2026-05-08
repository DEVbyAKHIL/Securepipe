FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install main deps first
RUN pip install --no-cache-dir -r requirements.txt

# Install checkov separately (it pins openai<1.0 internally, isolated)
RUN pip install --no-cache-dir checkov==3.1.43

# Force reinstall openai 1.x AFTER checkov (overrides checkov's old openai)
RUN pip install --no-cache-dir --force-reinstall openai==1.30.1

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]