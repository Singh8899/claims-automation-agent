FROM python:3.12-slim

# Working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Requirements copy and installation
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt 

# Copy needed codebase
COPY src/ ./src/
COPY .env .
COPY scripts/serve.py ./scripts/

EXPOSE 8000

# Run the service
CMD ["python", "scripts/serve.py"]
