import psycopg
import os
import csv
from parser import parser

# Constantes para dizer de onde vem o Schema do banco, as chunks que vem do parser (grupo de produtos)
# e o arquivo de origem do dado, altere para fazer sentido na sua pasta, só eu que coloquei em data/
SCHEMA = "sql/schema.sql"
CHUNK = 1000
ARQUIVO = "../data/amazon-meta.txt"

# Essa função fáz uma conexão com o postgres e retorna a conexão, pra manipular o BD
def conectar_postgres():
    try:
        con = psycopg.connect(
            host="db",
            port=5432,
            dbname="ecommerce",
            user="postgres",
            password="postgres")
        return con
    except Exception as error:
        print("Deu erro ae: ", error)
        return None

# essa funcao executa o schema.sql para estruturar o BD
def executar_script_sql(arquivo_sql, conexao):
    try:
        # Abrir o arquivo .sql
        with open(arquivo_sql, 'r') as f:
            script_sql = f.read()
        # Criar um cursor e executar o script SQL
        with conexao.cursor() as cursor:
            cursor.execute(script_sql)
            conexao.commit()
            print("Schema criado com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        conexao.rollback()
        conexao.close()
        return 1
    conexao.close()
    return 0

# essa funcao gera os csv individuais pra cada tabela
def gerar_csvs(parser, tmp_dir="/out"):
    os.makedirs(tmp_dir, exist_ok=True)

    products_csv = os.path.join(tmp_dir, "Product.csv")
    categories_csv = os.path.join(tmp_dir, "Categories.csv")
    prodcat_csv = os.path.join(tmp_dir, "Product_categories.csv")
    similar_csv = os.path.join(tmp_dir, "similar.csv")
    customer_csv = os.path.join(tmp_dir, "Customer.csv")
    reviews_csv = os.path.join(tmp_dir, "reviews.csv")

    with (open(products_csv, "w", newline="", encoding="utf-8") as f_prod, \
            open(categories_csv, "w", newline="", encoding="utf-8") as f_cat, \
            open(prodcat_csv, "w", newline="", encoding="utf-8") as f_prodcat, \
            open(similar_csv, "w", newline="", encoding="utf-8") as f_similar, \
            open(customer_csv, "w", newline="", encoding="utf-8") as f_customer, \
            open(reviews_csv, "w", newline="", encoding="utf-8") as f_reviews):

        writer_prod = csv.writer(f_prod)
        writer_cat = csv.writer(f_cat)
        writer_prodcat = csv.writer(f_prodcat)
        writer_similar = csv.writer(f_similar)
        writer_customer = csv.writer(f_customer)
        writer_reviews = csv.writer(f_reviews)

        customers = set()
        # product
        for produtos in parser(ARQUIVO, CHUNK):
            categories_set = set()
            prodcat_set = set()
            for dado in produtos:
                total_reviews = dado.get("total", None)
                if total_reviews is not None:
                    total_reviews = int(total_reviews)
                writer_prod.writerow((
                    dado.get("ASIN"),
                    dado.get("title", None),
                    dado.get("group", None),
                    dado.get("salesrank", None),
                    total_reviews
                ))

                if "categories" in dado and dado["categories"]:
                    for hierarquia in dado["categories"]:
                        hierarquia_reversa = list(reversed(hierarquia))
                        id_filho = None
                        for categoria_completa in hierarquia_reversa:
                            try:
                                nome = categoria_completa.split('[')[0].strip()
                                id_categoria = int(categoria_completa.split('[')[1].strip(']'))
                                tupla = (id_categoria, nome, id_filho)
                                if tupla not in categories_set:
                                    writer_cat.writerow((id_categoria, nome, id_filho))
                                    categories_set.add(tupla)
                                id_filho = id_categoria
                            except Exception as e:
                                print("erro em Categories:", e)
                                continue

                        #Product_categories
                        id_produto = int(dado.get("Id"))
                        for categoria_completa in hierarquia:
                            try:
                                id_categoria = int(categoria_completa.split('[')[1].strip(']'))
                                tupla = (id_produto, id_categoria)
                                if tupla not in prodcat_set:
                                    writer_prodcat.writerow((id_produto, id_categoria))
                                    prodcat_set.add(tupla)
                            except Exception as e:
                                print("erro em Product_categories:", e)
                                continue

                if "similar" in dado and dado["similar"]:
                    try:
                        similares = dado["similar"].split()
                        qnt = int(similares[0])
                        asin_list = similares[1:]

                        id_produto = int(dado.get("Id"))
                        for asin in asin_list:
                            values = (id_produto, asin)
                            writer_similar.writerow(values)
                    except Exception as e:
                        print("erro em Product_similar:", e)
                        continue

                if "reviews" in dado and dado["reviews"]:
                    reviews_produto = dado["reviews"]
                    id_produto = int(dado.get("Id"))
                    for r in reviews_produto:
                        customer_id = r.get("customer")
                        if customer_id not in customers:
                            writer_customer.writerow([customer_id])
                            customers.add(customer_id)
                        values = (
                            id_produto,
                            r.get("data"),
                            customer_id,
                            r.get("rating"),
                            r.get("votes"),
                            r.get("helpful")
                        )
                        writer_reviews.writerow(values)

    return products_csv, categories_csv, prodcat_csv, similar_csv, customer_csv, reviews_csv

# essa funcao passa para o banco dado uma tabela, as colunas e o caminho do arquivo csv
def COPY_FROM(con, tabela, colunas, caminho_csv):
    try:
        with con.cursor() as cursor: # abre o cursor pra executar scripts sql
            # Para a tabela Product
            if tabela == "Product":

                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_product(
                                asin VARCHAR(20),
                                title VARCHAR(500),
                                prod_group VARCHAR(300),
                                salesrank INTEGER,
                                total_review INTEGER
                                );"""
                cursor.execute(sql_tmp)

                # Lê do arquivo e copia pra tabela temporaria
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere os dados da tabela temporaria na tabela oficial
                # ignora conflitos caso o ASIN já exista em Product (evita duplicidade)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product 
                                ON CONFLICT (asin) DO NOTHING;
                                """
                cursor.execute(sql_tmp);

            # Para a tabela Categories
            elif tabela == "Categories":
                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_categories(
                                id_category INTEGER,
                                category_name TEXT,
                                id_category_father INTEGER
                            );"""
                cursor.execute(sql_tmp)

                # Copia os dados do CSV para a tabela temporária
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_categories FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere na tabela oficial os dados da tabela temporaria, ignorando conflitos de chave primaria
                # supondo que já esteja inserido
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_categories 
                                ON CONFLICT (id_category) DO NOTHING;
                            """
                cursor.execute(sql_tmp);

            # Para a tabela Product_categories
            elif tabela == "Product_categories":
                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_product_categories(
                                id_product INTEGER,
                                id_category_son INTEGER
                            );"""
                cursor.execute(sql_tmp)

                # copia os dados do CSV para a tabela temporaria
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product_categories FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere na tabela oficial os dados da tabela temporaria, ignorando conflitos de PK
                # supondo que já esteja inserido
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product_categories 
                                ON CONFLICT (id_product,id_category_son) DO NOTHING;
                            """
                cursor.execute(sql_tmp);

            # Para a tabela Product_similar
            elif tabela == "Product_similar":
                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_product_similar(
                                id_product INTEGER,
                                asin_similar VARCHAR(20)
                            );"""
                cursor.execute(sql_tmp)

                # Copia os dados do CSV para a tabela temporaria
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product_similar FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere na tabela oficial, garantindo que os produtos similares existam na tabela Product
                # ignora duplicidade na chave primaria composta (id_product, asin_similar) pq ja ta inserido
                sql_tmp = f"""INSERT INTO {tabela} ({colunas}) 
                                SELECT DISTINCT t.id_product, t.asin_similar 
                                FROM tmp_product_similar t
                                JOIN Product p ON t.asin_similar = p.asin
                                ON CONFLICT ({colunas}) DO NOTHING;
                            """
                cursor.execute(sql_tmp);

            # Para a tabela Customer
            elif tabela == "Customer":
                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_customer(
                                id_customer VARCHAR(20))
                            """
                cursor.execute(sql_tmp)

                # copia do csv pra tabela temporaria
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_customer FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere na tabela oficial os dados da tabela temporaria, ignora as duplicatas de PK
                sql_tmp = f"""INSERT INTO {tabela} ({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_customer 
                                ON CONFLICT ({colunas}) DO NOTHING;
                            """
                cursor.execute(sql_tmp);

            # Para a tabela Review
            elif tabela == "Review":
                # Cria uma tabela temporária para inserir dados do CSV
                # Evita validações de chave única ou de integridade para cada linha (mais rapido)
                sql_tmp = f"""CREATE TEMP TABLE tmp_review(
                                id_product INTEGER,
                                date DATE,
                                customer VARCHAR(20),
                                rating INTEGER,
                                votes INTEGER,
                                helpful INTEGER);
                            """
                cursor.execute(sql_tmp)

                # copia o csv pra tabela temporaria
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_review FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                # insere na tabela oficial os dados da tabela temporaria,
                # nao da conflito aqui pq o id é gerado automaticamente pelo postgres (SERIAL)
                # e na tabela temporaria nao tem SERIAL
                # o atributo customer é FK pra Customer, e o join garante integridade referencial
                sql_tmp = f"""INSERT INTO {tabela} ({colunas}) 
                                SELECT DISTINCT tmp.id_product, tmp.date, tmp.customer,
                                    tmp.rating, tmp.votes, tmp.helpful
                                FROM tmp_review tmp
                                JOIN Product p ON tmp.id_product = p.id_product
                                JOIN Customer c ON tmp.customer = c.id_customer;
                            """
                cursor.execute(sql_tmp);
        con.commit()
        print(f"{tabela} carregado com sucesso de {caminho_csv}")
    except Exception as e:
        con.rollback()
        print(f"erro ao carregar para {tabela}: {e}")

def main():
    # pega conexao
    con = conectar_postgres()

    #cria o schema do BD
    ret = executar_script_sql(SCHEMA, con)

    # se deu tudo certo, pega uma nova conexao com esse BD pq pra criar eu fecho a conexao
    if ret == 0:
        con = conectar_postgres()

    # gera os csv (gera no Docker, nao local)
    products_csv, categories_csv, prodcat_csv, similar_csv, customer_csv, review_csv = gerar_csvs(parser)
    # vai copiando do CSV pra tabela
    COPY_FROM(con, "Product", "asin, title, prod_group, salesrank, "
                              "total_review", products_csv)
    COPY_FROM(con, "Categories", "id_category, category_name, "
                                 "id_category_father", categories_csv)
    COPY_FROM(con, "Product_categories", "id_product, "
                                         "id_category_son", prodcat_csv)
    COPY_FROM(con, "Product_similar", "id_product, asin_similar", similar_csv)
    COPY_FROM(con, "Customer", "id_customer", customer_csv)
    COPY_FROM(con, "Review", "id_product, date, customer, rating,"
                             " votes, helpful", review_csv)


    # isso aqui era pra ver se tava inserindo no BD mesmo
    # da pra mudar a tabela e brincar com os joins da vida.
    # printa as tuplas de retorno no terminal
    #with con.cursor() as cur:
    #    cur.execute("SELECT * FROM Review;")  # pega as 20 primeiras linhas
    #    for row in cur.fetchall():
    #        print(row)

    # se abriu tem que fechar ne, educacao em dia
    con.close()

# executa a main
main()