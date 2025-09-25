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
	docker compose run --rm app python src/index.py

parser:
	docker compose run --rm app python src/parser.py

dashboard:
	docker compose run --rm app python src/dashboard.py --db-password postgres

health:
	docker compose ps

help:
	@echo "Comandos disponíveis:"
	@echo "  make up         - sobe containers em background (com build)"
	@echo "  make down       - derruba os containers"
	@echo "  make build      - reconstrói as imagens"
	@echo "  make restart    - reinicia containers"
	@echo "  make test       - executa script de teste de conexão"
	@echo "  make dashboard  - executa script das consultas para o dashboard"
	@echo "  make health     - mostra saúde dos serviços do docker compose"
	@echo "  make help       - mostra esta ajuda"
