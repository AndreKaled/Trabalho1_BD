import psycopg
import os
import csv
from parser import parser
import argparse

SCHEMA = "sql/schema.sql"
CHUNK = 1000

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

def gerar_csvs(parser, arquivo, tmp_dir="/out"):
    os.makedirs(tmp_dir, exist_ok=True)

    products_csv = os.path.join(tmp_dir, "Product.csv")
    categories_csv = os.path.join(tmp_dir, "Categories.csv")
    prodcat_csv = os.path.join(tmp_dir, "Product_categories.csv")
    similar_csv = os.path.join(tmp_dir, "Product_similar.csv")
    review_csv = os.path.join(tmp_dir, "Review.csv")
    customer_csv = os.path.join(tmp_dir, "Customers.csv")

    with open(products_csv, "w", newline="", encoding="utf-8") as f_prod, \
            open(categories_csv, "w", newline="", encoding="utf-8") as f_cat, \
            open(prodcat_csv, "w", newline="", encoding="utf-8") as f_prodcat, \
            open(similar_csv, "w", newline="", encoding="utf-8") as f_sim, \
            open(customer_csv, "w", newline="", encoding="utf-8") as f_cus, \
            open(review_csv, "w", newline="", encoding="utf-8") as f_rev:

        writer_prod = csv.writer(f_prod)
        writer_cat = csv.writer(f_cat)
        writer_prodcat = csv.writer(f_prodcat)
        writer_similar = csv.writer(f_sim)
        writer_review = csv.writer(f_rev)
        writer_customer = csv.writer(f_cus)

        #review_id = 0 Saiuuu pq não precisamos, o domínio Serial faz a incrementação sozinhooo
        num_pacotes = 0


        #foi adicionado uma lista para conter todos os ASIN do arquivo pois o similar usar ASIN e referencia o ASIN do Product(ASIN).
        categories_set = set()
        prodcat_set = set()
        asin_list = set()
        customers = set()



        # product
        for produtos in parser(arquivo, CHUNK):

            print(f"FORAM ADICIONADOS {num_pacotes} Produtos, E ESTÁ SENDO INICIADO O PARSER DE UM NOVO PACOTE DE PRODUTOS")
            if(num_pacotes>=1000):
               break
            print(len(produtos))


            for dado in produtos:
                print(f"Produtos número {num_pacotes} sendo carregado.")


                if(len(dado) < 3):
                    continue
                total_reviews = dado.get("total", None)
                if total_reviews is not None:
                    total_reviews = int(total_reviews)
                #Adicionando o id_product na tupla de f_prod, tirar totais 
                writer_prod.writerow((
                    int(dado.get("Id")),
                    dado.get("ASIN"),
                    dado.get("title", None),
                    dado.get("group", None),
                    total_reviews,
                    dado.get("salesrank", None),
                    dado.get("avg_rating", None),
                    
                ))
                asin_list.add((dado.get("ASIN")))


                if "categories" in dado and dado["categories"]:
                    print("Carregando categories")
                    for hierarquia in dado["categories"]:
                        hierarquia_reversa = list(reversed(hierarquia))
                        id_filho = None
                        for categoria_completa in hierarquia_reversa:
                            try:
                                nome = categoria_completa.split('[')[0].strip()
                                id_categoria = int(categoria_completa.split('[')[-1].strip(']'))
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
                        # Foi trocada a hierarquia por hierarquia_reversa, pois estava selecionando a primeira categoria da hierarquia(maior pai).
                        for categoria_completa in hierarquia_reversa:
                            try:
                                id_categoria = int(categoria_completa.split('[')[-1].strip(']'))
                                tupla = (id_produto, id_categoria)
                                if tupla not in prodcat_set:
                                    writer_prodcat.writerow((id_produto, id_categoria))
                                    prodcat_set.add(tupla)
                            except Exception as e:
                                print("erro em Product_categories:", e)
                                continue
                            
                if("similar" in dado and dado["similar"]):
                    print("Carregando similares")
                    id_produto = int(dado.get("Id"))
                    similares = dado["similar"].split("  ")
                    for asin_similar in similares:
                        try:
                            if asin_similar.strip() in asin_list:
                                writer_similar.writerow((id_produto, asin_similar.strip()))
                        except Exception as e:
                            print("erro em Product_similar:", e)
                            continue

                if 'reviews' in dado and dado['reviews']:
                    print("Carregando reviews")
                    id_produto = int(dado.get("Id"))

                    for review in dado['reviews']:
                        try:
                            #id_review = review_id Saiu pq implementa sozinhoooooooooo
                            id_produto = id_produto
                            data = review['data']
                            customer = review['customer']
                            rating = review['rating']
                            votes = review['votes']
                            helpful = review['helpful']

                            if(customer not in customers):
                                writer_customer.writerow([customer])
                                customers.add((customer))

                            if(customer in customers):    
                                #values = (int(id_review), id_produto, data, customer, rating, votes, helpful)
                                values = ( id_produto, data, customer, rating, votes, helpful) #id_rivew saiu porque é serial e implementa sozinho

                                print(values) #Printa as tuplas das reviews     RETIRAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA!!!!
                                writer_review.writerow(values)
                                #id_review +=1 Saiuuuu pq o domínio SERIAL incrementa sozinho
                            else:
                                print("Customer da review não está em customers")

                        except Exception as e:
                            print("deu erro em Review:", e)
                            continue
                num_pacotes += 1
                    
                            
    return similar_csv, products_csv, categories_csv, prodcat_csv, review_csv, customer_csv

def COPY_FROM(con, tabela, colunas, caminho_csv):
    try:
        with con.cursor() as cursor:
            if tabela == "Product":
                sql_tmp = f"""CREATE TEMP TABLE tmp_product(
                                id_product SERIAL,
                                asin VARCHAR(20),
                                title VARCHAR(500),
                                prod_group VARCHAR(300),
                                total_review INTEGER,
                                salesrank INTEGER,
                                avg_rating FLOAT
                                );"""
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product 
                                ON CONFLICT (id_product) DO NOTHING;
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
                                SELECT DISTINCT {colunas} FROM tmp_product_categories ;
                            """
                cursor.execute(sql_tmp);
            
            elif tabela == "Product_similar":
                sql_tmp = f"""CREATE TEMP TABLE tmp_product_similar(
                                id_product INTEGER,
                                asin_similar VARCHAR(20)
                            );"""
                cursor.execute(sql_tmp)
                #falta fazer o caminho_csv
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_product_similar FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas}) 
                                SELECT DISTINCT {colunas} FROM tmp_product_similar;
                            """
                cursor.execute(sql_tmp);
            
            #ADICIONADA RECENTEMENTE.
            elif tabela == "Review":
                sql_tmp = """CREATE TEMP TABLE tmp_review(
                        id_product INTEGER,
                        data_review DATE, customer VARCHAR(20), 
                        rating  INTEGER, votes INTEGER, helpful INTEGER);"""
                
                        #id_review SERIAL,  Saiu da criação da tabela CREAT TEMP TABLE pq o domínio SERIAL incremeneta sozinhooo
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_review({colunas}) FROM STDIN CSV") as copy:
                        copy.write(f.read())


                sql_tmp = f"""INSERT INTO {tabela}({colunas})
                SELECT {colunas} FROM tmp_review;
                            """
                cursor.execute(sql_tmp)

                #Não entendi o pq não precisa incrementar nas linhas, apenas insere direto, mas funcionou  NÃO MECHAAAAAA É PERIGOSOOOOOOOOOO
                '''
                    with cursor.copy(f"COPY tmp_review FROM STDIN CSV") as copy:
                        for linha in f:
                            print(linha)
                            copy.write(linha)
                sql_tmp = f"""INSERT INTO {tabela}({colunas})
                            SELECT DISTINCT {colunas} FROM tmp_review;
                            """
                            #ON CONFLICT (id_review) DO NOTHING;'''
            
            #INSERÇÃO DA TABELA CUSTOMER:
            elif tabela == "Customer":
                sql_tmp = """CREATE TEMP TABLE tmp_customer(
                        id_customer VARCHAR(14))"""
                
                cursor.execute(sql_tmp)
                with open(caminho_csv, "r", encoding="utf-8") as f:
                    with cursor.copy(f"COPY tmp_customer FROM STDIN CSV") as copy:
                        for linha in f:
                            copy.write(linha)

                sql_tmp = f"""INSERT INTO {tabela}({colunas})
                            SELECT DISTINCT {colunas} FROM tmp_customer
                            ON CONFLICT (id_customer) DO NOTHING;
                            """
                cursor.execute(sql_tmp);
                    
        con.commit()
        print(f"{tabela} carregado com sucesso de {caminho_csv}")
    except Exception as e:
        con.rollback()
        print(f"erro ao carregar para {tabela}: {e}")

def main():
    arg_parser = argparse.ArgumentParser(description="Script para popular dados no Banco de dados")

    arg_parser.add_argument(
        '--input',
        type=str,
        default='../data/amazon-meta.txt',
        help='Host do banco de dados.')
    args = arg_parser.parse_args()
    arquivo_input = args.input

    print(f"Tentando carregar dados do arquivo: {arquivo_input}")

    con = conectar_postgres()
    ret = executar_script_sql(SCHEMA, con)
    if ret == 0:
        con = conectar_postgres()

    similar_csv, products_csv, categories_csv, prodcat_csv, review_csv, customer_csv = gerar_csvs(parser, arquivo_input)
    #Foi adicionaodo a chave do produto e a avg_rating na funcao COPY_FROM
    COPY_FROM(con, "Product", "id_product, asin, title, prod_group, total_review, salesrank, avg_rating", products_csv)
    COPY_FROM(con, "Categories", "id_category, category_name, id_category_father", categories_csv)
    COPY_FROM(con, "Product_categories", "id_product, id_category_son", prodcat_csv)
    COPY_FROM(con, "Product_similar", "id_product, asin_similar", similar_csv)
    COPY_FROM(con, "Customer", "id_customer", customer_csv)
    #COPY_FROM(con, "Review", "id_review, id_product, data_review, customer, rating, votes, helpful", review_csv) MUDOU POIS NÃO PRECISA INSERIR ID_REVIEW O DOMÍNIO SERIAL INCREMENTA SOZINHO 
    COPY_FROM(con, "Review",  "id_product, data_review, customer, rating, votes, helpful", review_csv)

    con.close()

main()