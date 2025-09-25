# define imagem base
FROM python:3.11-alpine

# define diretorio de trabalho do container
WORKDIR /app

#copia e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia os arquivos do src para a pasta raiz do container
COPY src/ ./src
COPY sql/ ./sql

# executa os comandos a seguir:
CMD ["python","src/index.py"]