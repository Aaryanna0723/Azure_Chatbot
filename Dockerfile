FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
COPY en_core_web_sm-3.8.0-py3-none-any.whl /app/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 

RUN pip install /app/en_core_web_sm-3.8.0-py3-none-any.whl

EXPOSE 7860
CMD ["python", "app.py"]