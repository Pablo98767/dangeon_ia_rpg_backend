# Use uma imagem base Python oficial
FROM python:3.10-slim

# Defina o diretório de trabalho no container
WORKDIR /usr/src/app

# Copie o arquivo de requisitos e instale as dependências
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da sua aplicação
COPY . .

# Comando para rodar o servidor Uvicorn.
# Substitua 'main:app' pelo nome do seu arquivo principal e da sua instância FastAPI, se forem diferentes.
# O Back4App injeta a variável de ambiente PORT. Sua aplicação DEVE escutar nela.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
