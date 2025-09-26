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
## 1. Inicialização do Ambiente
   Use o comando abaixo para construir as imagens (se necessário) e iniciar os serviços db (PostgreSQL) e app (Aplicação Python) em background.
   ```bash 
   make up
   ```

### Gerenciando o ambiente
- `make down` derruba (para) os contêineres e remove os volumes.
```bash
    make down
```
- `make build` reconstrói as imagens do Docker, sem subir os contêineres.
```bash
    make build
```
- `make restart` Derruba e sobe os contêineres novamente (make up e make down)
```bash
    make restart
```
- Ajuda? use `make help`

## 2. Carga de Dados e Criação de Esquema (make carga)
O script de carga (src/tp1_3.2.py) cria o esquema do banco de dados e carrega os dados do arquivo de input. 
Por padrão, ele tenta carregar o arquivo em ```../data/amazon-meta.txt``` (o default do script Python).

Uso Padrão (Arquivo Default)
```bash
    make carga
```
Carregando um Arquivo Específico
Você pode especificar o caminho do arquivo de dados (que deve estar acessível dentro do contêiner, 
geralmente montado via volume, ex: /data/). Use a variável INPUT_FILE.
```bash
    make carga INPUT_FILE="../data/nome.txt"
```
Uso com argumentos (usando o arquivo padrao)

Uso com argumentos e o arquivo específico

docker compose run --rm app python src/tp1_3.2.py \
--db-host db --db-port 5432 --db-name ecommerce --db-user postgres --db-pass postgres \
--input /data/snap_amazon.txt

## 4) Executar o Dashboard (todas as consultas)
O script do Dashboard (src/dashboard.py) executa consultas no banco de dados. 
Ele é flexível e permite que você passe argumentos para sobrescrever as configurações de conexão 
(como host, porta, senha, etc.)

Usando a Senha Padrão

O make assume a senha postgres, que é a senha padrão do seu contêiner.
```bash
    make dashboard
```

Passando Apenas a Senha

Use a variável DB_PASSWORD para definir uma senha específica, mantendo as outras configurações padrão 
(host: db, port: 5432, etc.).
```bash
    make dashboard DB_PASSWORD='senha_secreta'
```

Passando Múltiplos Argumentos (Avançado)

Use a variável ARGS com aspas duplas para passar qualquer combinação de argumentos suportados 
pelo script Python (--db-host, --db-port, --output-dir, --product-asin, etc.).

```bash
    # Definindo porta e diretório de saída, além da senha
    make dashboard ARGS="--db-port 5444 --db-password nova_senha --output-dir /app/custom_out"
```