import psycopg
import os
import csv
from parser import parser

SCHEMA = "sql/schema.sql"
CHUNK = 1000
ARQUIVO = "../data/amazon-meta.txt"


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

def COPY_FROM_STDIN(dados, tabela, colunas, conexao):
    try:
        sql = f"""COPY {tabela}({colunas}) FROM STDIN"""
        cursor = conexao.cursor()
        dados_pra_copiar = []
        if tabela == "Product":
            for dado in dados:
                total_reviews = dado.get("total",None)
                if total_reviews is not None:
                    total_reviews = int(total_reviews)
                values = (
                    dado.get("ASIN"),
                    dado.get("title", None),
                    dado.get("group", None),
                    dado.get("salesrank", None),
                    total_reviews)
                dados_pra_copiar.append(values)

        elif tabela == "Categories":
            sql_tmp = """CREATE TEMP TABLE tmp_categories(
                            id_category INTEGER,
                            category_name VARCHAR(100),
                            id_category_father INTEGER
                         );"""
            cursor = conexao.cursor()
            cursor.execute(sql_tmp)
            sql_tmp = f"""COPY tmp_categories({colunas}) FROM STDIN"""
            for dado in dados:
                if "categories" in dado and dado["categories"]:
                    for hierarquia in dado["categories"]:
                        hierarquia_reversa = list(reversed(hierarquia))
                        id_filho = None
                        for categoria_completa in hierarquia_reversa:
                            try:
                                nome = categoria_completa.split('[')[0].strip()
                                id_categoria = int(categoria_completa.split('[')[1].strip(']'))

                                # ve se ja ta na lista
                                values = (id_categoria, nome, id_filho)
                                if values not in dados_pra_copiar:
                                    dados_pra_copiar.append(values)
                                id_filho = id_categoria
                            except Exception as e:
                                print("deu erro patrao:", e)
                                continue
            if dados_pra_copiar:
                with cursor.copy(sql_tmp) as copy:
                    for linha in dados_pra_copiar:
                        copy.write_row(linha)
            sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                        SELECT DISTINCT {colunas} FROM tmp_categories
                        ON CONFLICT (id_category) DO NOTHING;
                      """
            cursor.execute(sql_tmp)
            cursor.execute("DROP TABLE IF EXISTS tmp_categories;")
            conexao.commit()
            dados_pra_copiar = None

        elif tabela == "Product_categories":
            sql_tmp = """CREATE TEMP TABLE tmp_product_categories(
                        id_product INTEGER, id_category_son INTEGER);"""
            cursor = conexao.cursor()
            cursor.execute(sql_tmp)
            sql_tmp = f"""COPY tmp_product_categories({colunas}) FROM STDIN;"""
            for produto in dados:
                id_produto = int(produto.get("Id"))
                if 'categories' in produto and produto['categories']:
                    for hierarquia in produto['categories']:
                        for categoria_completa in hierarquia:
                            try:
                                id_categoria = int(categoria_completa.split('[')[1].strip(']'))
                                values = (id_produto, id_categoria)
                                dados_pra_copiar.append(values)
                            except Exception as e:
                                print("deu erro em Product_categories:", e)
                                # continua a inserir os outros
                                continue
            if dados_pra_copiar:
                with cursor.copy(sql_tmp) as copy:
                    for linha in dados_pra_copiar:
                        copy.write_row(linha)
            sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                            SELECT DISTINCT {colunas} FROM tmp_product_categories
                            ON CONFLICT ({colunas}) DO NOTHING;
                        """
            cursor.execute(sql_tmp)
            cursor.execute("DROP TABLE IF EXISTS tmp_product_categories;")
            conexao.commit()
            dados_pra_copiar = None

        if dados_pra_copiar:
            with cursor.copy(sql) as copy:
                for linha in dados_pra_copiar:
                    copy.write_row(linha)
        conexao.commit()
    except Exception as e:
        conexao.rollback()
        print(f"erro no copy para a tabela {tabela}: {e}")

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

def gerar_csvs(parser, tmp_dir="/out"):
    os.makedirs(tmp_dir, exist_ok=True)

    products_csv = os.path.join(tmp_dir, "Product.csv")
    categories_csv = os.path.join(tmp_dir, "Categories.csv")
    prodcat_csv = os.path.join(tmp_dir, "Product_categories.csv")

    with open(products_csv, "w", newline="", encoding="utf-8") as f_prod, \
            open(categories_csv, "w", newline="", encoding="utf-8") as f_cat, \
            open(prodcat_csv, "w", newline="", encoding="utf-8") as f_prodcat:

        writer_prod = csv.writer(f_prod)
        writer_cat = csv.writer(f_cat)
        writer_prodcat = csv.writer(f_prodcat)

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

    return products_csv, categories_csv, prodcat_csv

def COPY_FROM(con, tabela, colunas, caminho_csv):
    try:
        with con.cursor() as cursor:
            if tabela == "Product":
                sql_tmp = f"""CREATE TEMP TABLE tmp_product(
                                asin VARCHAR(20),
                                title VARCHAR(500),
                                prod_group VARCHAR(300),
                                salesrank INTEGER,
                                total_review INTEGER
                                );"""
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product 
                                ON CONFLICT (asin) DO NOTHING;
                                """
                cursor.execute(sql_tmp);
            elif tabela == "Categories":
                sql_tmp = f"""CREATE TEMP TABLE tmp_categories(
                                id_category INTEGER,
                                category_name TEXT,
                                id_category_father INTEGER
                            );"""
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_categories FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_categories 
                                ON CONFLICT (id_category) DO NOTHING;
                            """
                cursor.execute(sql_tmp);
            elif tabela == "Product_categories":
                sql_tmp = f"""CREATE TEMP TABLE tmp_product_categories(
                                id_product INTEGER,
                                id_category_son INTEGER
                            );"""
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product_categories FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product_categories 
                                ON CONFLICT (id_product,id_category_son) DO NOTHING;
                            """
                cursor.execute(sql_tmp);

        con.commit()
        print(f"{tabela} carregado com sucesso de {caminho_csv}")
    except Exception as e:
        con.rollback()
        print(f"erro ao carregar para {tabela}: {e}")

def main():
    con = conectar_postgres()
    ret = executar_script_sql(SCHEMA, con)
    if ret == 0:
        con = conectar_postgres()

    products_csv, categories_csv, prodcat_csv = gerar_csvs(parser)
    COPY_FROM(con, "Product", "asin, title, prod_group, salesrank, total_review", products_csv)
    COPY_FROM(con, "Categories", "id_category, category_name, id_category_father", categories_csv)
    COPY_FROM(con, "Product_categories", "id_product, id_category_son", prodcat_csv)

    #for produtos in parser(ARQUIVO, CHUNK):
    #    COPY_FROM_STDIN(produtos, "Product", "asin, title, prod_group, salesrank, total_review", con)
    #    COPY_FROM_STDIN(produtos, "Categories", "id_category, category_name, id_category_father", con)
    #    COPY_FROM_STDIN(produtos, "Product_categories", "id_product, id_category_son", con)
    con.close()

main()