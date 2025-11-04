FROM python:3.10-slim

WORKDIR /usr/src/app

# Copia o requirements.txt da pasta app
COPY ./app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da pasta app
COPY ./app ./

# Executa o servidor FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
