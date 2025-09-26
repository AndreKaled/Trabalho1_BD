.PHONY: up down build restart test help health

# sobe containers em background com build
up:
	docker compose up -d --build

# derruba os containers
down:
	docker compose down

# reconstroi imagens do docker
build:
	docker compose build

# reinicia
restart: down up

# testa o script para conexao do postgres
test:
ifdef INPUT_FILE
	docker compose run --rm app python src/index.py --input $(INPUT_FILE)
else
	docker compose run --rm app python src/index.py
endif

parser:
	docker compose run --rm app python src/parser.py

dashboard:
ifdef ARGS
# aceita os argumentos dados
	docker compose run --rm app python src/dashboard.py $(ARGS)
else
ifdef DB_PASSWORD
# aceita se for so a senha
	docker compose run --rm app python src/dashboard.py --db-password $(DB_PASSWORD)
else
# assume a senha padrao (postgres)
	docker compose run --rm app python src/dashboard.py --db-password postgres
endif
endif

health:
	docker compose ps

help:
	@echo "Comandos disponíveis:"
	@echo "  make up         				- sobe containers em background (com build)"
	@echo "  make down       				- derruba os containers"
	@echo "  make build      				- reconstrói as imagens"
	@echo "  make restart    				- reinicia containers"
	@echo "  make test       				- executa o script de carga, com arquivo de dados padrão '../data/amazon-meta.txt'"
	@echo "  make test INPUT_FILE='../data/NOME.txt'	- executa o script de carga com o arquivo do argumento (copie o arquivo para /data/)"
	@echo "  make dashboard  				- executa dashboard com senha padrao"
	@echo "  make dashboard DB_PASSWORD='senha_daora'	- executa o dashboard com a senha definida"
	@echo "  make dashboard ARGS='--db-port ...'		- executa o dashboard com todos os argumentos docker"
	@echo "  make health     				- mostra saúde dos serviços do docker compose"
	@echo "  make help       				- mostra essa ajuda"
