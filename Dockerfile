FROM python:3.10-slim

WORKDIR /usr/src/app

# Copia o requirements.txt da pasta app
COPY app/requirements.txt ./

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo da pasta app
COPY app/ ./

# Expõe a porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação (corrigido --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
