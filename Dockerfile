FROM python:3.10-slim

WORKDIR /usr/src

# Copia o requirements.txt da pasta app
COPY app/requirements.txt ./app/

# Instala as dependências
RUN pip install --no-cache-dir -r app/requirements.txt

# Copia todo o conteúdo da pasta app mantendo a estrutura
COPY app/ ./app/

# Expõe a porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação
# Agora o Python encontrará app.core.config corretamente
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
