# Introdução ao Docker


Iniciei uma breve introdução ao docker com [este vídeo do Diolinux](https://youtu.be/ntbpIfS44Gw?si=0jiMhuN09nM7tJTJ)  que é uma ótima introdução, também tem [este vídeo do Fábio Akita](https://youtu.be/85k8se4Zo70?si=CRFSKpVuatMIGftI) que é mais detalhado e técnico, também estou vendo [este vídeo do Fiasco](https://youtu.be/7YmLbhiK-PM?si=nf8rMF5VHmqAwaV4) que tem uma "pegada" mais prática.    
Diferentemente das VMs (Virtual Machines), um contâiner docker consegue compartilhar recursos da própria máquina hospedeira (kernel e hardware). Isso para reduzir a redundância e garantir um nível de segurança ao isolar contâiners uns dos outros.

# Tá, mas o que é um contâiner?

Um contêiner é uma forma de isolar uma aplicação e as suas dependências, permitindo que ela seja executada de forma consistente em diferentes ambientes.

# Características de um docker

* Isolamento: Os contêineres são isolados uns dos outros, o que significa que cada aplicação roda em seu próprio ambiente sem interferir nas outras.
* Compartilhamento de recursos: Diferentemente das máquinas virtuais, os contêineres compartilham o kernel do sistema operacional hospedeiro. Isso evita a redundância de ter vários sistemas operacionais completos rodando, resultando em um uso mais eficiente de recursos como processador, RAM e armazenamento.
* Otimização: Por não precisarem de um sistema operacional completo para cada aplicação, os contêineres são mais leves e consomem menos recursos.

# Instalação (Linux)

Se estiver usando uma distro que use o apt, use o seguinte comando:
```bash
sudo apt install docker.io docker-compose
```
Se quiser pode reiniciar o computador, se não, tem esse jeitinho aqui:
```bash
sudo systemctl enable --now docker docker.socket containerd
```
Para testar se tá rodando, use:
```bash
docker --help
```
Se estiver louco o bastante pra usar Arch, tem no gerenciador de pacotes padrão do pacman:
```bash
sudo pacman -S docker docker-compose
```
Para habilitar usei o seguinte
```bash
sudo systemctl enable --now docker.service
```

# Baixando uma imagem docker
O comando `docker pull` é usado para baixar uma imagem do Docker de um repositório para o computador.     
Detalhe: a imagem é base, que pode ser usado para criar N contâiners

Como o nosso projeto vai usar Python e PostgreSQL, vou listar como baixa e sobe um contâiner com eles aqui.

O comando `docker pull python` baixa uma imagem do Python do Docker Hub.    
O comando `docker pull postgres` baixa uma imagem do PostgreSQL do Docker Hub.

# Gerenciando um docker contâiner...

### Criando e rodando um contâiner único

Aqui vamos focar no PostgreSQL como exemplo, pq é um serviço de longa duração ideal para ser usado como contêiner.    
O comando abaixo cria e inicia um contêiner para o PostgreSQL.

```bash
docker run --name container_postgres -p 5432:5432 -e POSTGRES_PASSWORD=root -d postgres
```

Em resumo, segue uma explicação dos parâmetros:

`docker run`: Cria e inicia o contêiner.

`--name container_postgres`: Define um nome para o nosso contêiner (container\_postgres).

`-p 5432:5432`: Este é o mapeamento de portas. Ele faz uma "ponte" entre a porta 5432 do seu computador (lado esquerdo) e a porta 5432 de dentro do contêiner (lado direito). Com isso, você pode se conectar ao banco de dados do seu computador usando localhost:5432.

`-e POSTGRES_PASSWORD=root`: Define a variável de ambiente POSTGRES\_PASSWORD, que a imagem do PostgreSQL exige para definir a senha do usuário padrão.

`-d postgres`: Inicia o contêiner em segundo plano usando a imagem postgres

Nisso temos o seu contâiner rodando postgres 😃

### Removendo um contâiner

Para remover, primeiro precisamos parar o serviço, usa-se o comando `docker stop container_name` para isso.

```bash
docker stop container_postgres
```

e só então se remove:

```bash
docker rm container_postgres
```

Depois de removido, pode consultar os serviços docker rodando com o comando `docker ps -a`

# Dockerfile

[Video base da configuração](https://youtu.be/8HeGvqQxpZU?si=jucy2Nonu4YsZyUy)

```dockerfile
# define imagem base
FROM python:3.13

# define diretorio de trabalho do container
WORKDIR /app

[#copia](project/michaelwpv-trab-bd/t/copia) e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia os arquivos do src para a pasta raiz do container
COPY src/ ./src

# executa os comandos a seguir:
CMD ["python","src/index.py"]
```

Atente-se que index é apenas um arquivo de teste que imprime 'oi'

Para preparar a execução, basta usar o comando build a seguir:

```bash
docker build -t dc-python .
```

ps: dc-python será o nome da Imagem.

E depois use o seguinte comando para rodar, com o nome de container teste:

```bash
docker run -it --name teste dc-python
```

Pronto, o arquivo index.py será executado, ou qualquer outro programa escrito na tag CMD do dockerfile
