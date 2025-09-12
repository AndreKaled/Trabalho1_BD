# Trabalho Prático 1 – Bancos de Dados I

Este repositório contém a solução do TP1 da disciplina 
**Bancos de Dados I (2025/02)**.  
O ambiente é conteinerizado com **Docker** e **Docker Compose**, 
sem dependências locais além destes

O trabalho está fazendo uso do MakeFile para agilizar o uso de comandos docker,
se preferir podes usar os comandos próprios do ```docker``` e ```docker compose```.
Ou siga os passos abaixo com o Makefile, se desejar use o ```make help``` para
ajuda com os comandos.

---

## 1) Construir e subir os serviços
```bash
   make up
```
O comando executa exatamente isto:
```bash
    docker compose up -d --build
```

## 2) (Opcional) conferir saúde do PostgreSQL
```bash
    make health
```
O comando executa exatamente isto:
```bash
    docker compose ps
```

## Teste da conexão com o postgres
```bash
    make test
```
O comando executa exatamente isto: 
```bash
    docker compose run --rm app python src/index.py
```

---
# A partir daqui está em desenvolvimento
## 3) Criar esquema e carregar dados
docker compose run --rm app python src/tp1_3.2.py \
--db-host db --db-port 5432 --db-name ecommerce --db-user postgres --db-pass postgres \
--input /data/snap_amazon.txt

## 4) Executar o Dashboard (todas as consultas)
docker compose run --rm app python src/tp1_3.3.py \
--db-host db --db-port 5432 --db-name ecommerce --db-user postgres --db-pass postgres \
--output /app/out
