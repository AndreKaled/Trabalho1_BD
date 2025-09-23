import psycopg
from parser import parser

SCHEMA = "sql/schema.sql"
CHUNK = 150
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
        with cursor.copy(sql) as copy:
            for dado in dados:
                id = dado.get("Id")
                asin = dado.get("ASIN")
                title = dado.get("title", None)
                prod_group = dado.get("group", None)
                salesrank = dado.get("salesrank", None)
                total_review = dado.get("review", None)
                total_review = total_review['total'] if total_review else None

                values = (asin,title,prod_group, salesrank, total_review)

                copy.write_row(values)
                print(f"COPIADO O ITEM: {dado.get('Id')}")
    except Exception as e:
        print(f"erro: {e}")

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

def selectProduto(con):
    try:
        cursor = con.cursor()
        sql = """SELECT * FROM Product"""
        consulta = cursor.execute(sql)

        print(f"select deu isso ae:")
        for linha in consulta:
            print(linha)

        return 0
    except Exception as e:
        print(f"erro ao buscar na tabela Product: {e}")
        con.rollback()
        return 1

def populaProduto(con, produtos):
    try:
        cursor = con.cursor()
        sql = """INSERT INTO Product (asin, title, prod_group,
               salesrank, total_review) 
               VALUES (%s, %s, %s, %s, %s);"""
        for produto in produtos:
            salesrank = int(produto.get('salesrank', 0))
            total_review = int(produto.get('total_review', 0))

            values = (
                produto.get('ASIN'),
                produto.get('title', 'NULL'),
                produto.get('group', 'NULL'),
                salesrank,
                total_review
            )
            cursor.execute(sql, values)
        con.commit()
        print(f"inserido {len(produtos)} produtos da tabela Product")
        return 0
    except Exception as e:
        print(f"erro ao popular a tabela Product: {e}")
        con.rollback()
        return 1

def populaCategoria(con, produtos):
    try:
        cursor = con.cursor()
        total_categorias_inseridas = 0
        sql = """INSERT INTO Categories(id_category, 
                 category_name, id_category_father) 
                 VALUES(%s, %s, %s)
                 ON CONFLICT (id_category) DO NOTHING;
              """
        sql2 = """
               INSERT INTO Product_categories(id_product, id_category_son)
               VALUES(%s, %s)
               ON CONFLICT DO NOTHING;
               """
        for produto in produtos:
            id_produto = int(produto.get('Id'))

            if 'categories' in produto and produto['categories']:
                total_categorias_inseridas += len(produto['categories'])
                for hierarquia in produto['categories']:
                    hierarquia = list(reversed(hierarquia))
                    id_filho = None
                    for categoria in hierarquia:
                        nome = categoria.split('[')[0]
                        id_categoria = int(categoria.split('[')[1].split(']')[0])

                        cursor.execute(sql, (id_categoria, nome, id_filho))
                        cursor.execute(sql2, (id_produto, id_categoria))
                        id_filho = id_categoria
        con.commit()
        print(f"inserindo {total_categorias_inseridas} categorias da tabela Categoria")
        print(f"tambem insere a relacao na tabela Product_categories")
    except Exception as e:
        print(f"erro ao inserir na tabela Category: {e}")
        return 1

def selectCategory(con):
    try:
        cursor = con.cursor()
        sql = """SELECT * FROM Categories"""
        consulta = cursor.execute(sql)

        print(f"select deu isso ae:")
        for linha in consulta:
            print(linha)

        return 0
    except Exception as e:
        print(f"erro ao buscar na tabela Product: {e}")
        con.rollback()
        return 1

def populaReview(con, produtos):
    try:
        cursor = con.cursor()
        cont = 0
        sql = """
                INSERT INTO Review(id_product, date, customer, 
                rating, votes, helpful) 
                VALUES (%s,%s,%s,%s,%s,%s)
              """
        sql_customer = """
                        INSERT INTO Customer(id_customer)
                        VALUES (%s) ON CONFLICT (id_customer) DO NOTHING;
                       """
        for produto in produtos:
            id_produto = int(produto.get('Id'))
            for review in produto['reviews']:
                customer = review.get('customer')
                date = review.get('date')
                rating = int(review.get('rating'))
                votes = int(review.get('votes'))
                helpful = int(review.get('helpful'))
                cursor.execute(sql_customer, (customer,))
                values = (
                    id_produto,
                    date,
                    customer,
                    rating,
                    votes,
                    helpful
                )
                cursor.execute(sql, values)
                cont+=1
        con.commit()
        print(f"inserindo {cont} reviews na tabela Review")
    except Exception as error:
        print(f"erro ao inserir na tabela Review: {error}")

def populaSimilar(con, produtos):
    try:
        cursor = con.cursor()
        cont = 0
        sql_select_asin = """SELECT id_product FROM Product WHERE asin = %s"""
        sql = """INSERT INTO Product_similar(id_product, asin_similar)
              VALUES (%s,%s) ON CONFLICT DO NOTHING;"""
        for produto in produtos:
            id_produto = int(produto.get('Id'))
            asin_principal = produto.get('ASIN')
            if 'similar' in produto and produto['similar']:
                for asin_similar in produto['similar']:
                    if asin_principal == asin_similar: continue
                    cursor.execute(sql_select_asin, (asin_similar,))
                    result = cursor.fetchone()
                    if result:
                        asin_similar = result[0]
                        cursor.execute(sql, (id_produto, asin_similar))
                        cont+=1
        con.commit()
        print(f"inserindo {cont} similares na tabela Product_similar")
    except Exception as e:
        print(f"erro ao inserir na tabela Similar: {e}")

# tentar mudar pra usar COPY
def main():
    con = conectar_postgres()
    ret = executar_script_sql(SCHEMA, con)
    if ret == 0:
        con = conectar_postgres()
    cont = 0

    for produtos in parser(ARQUIVO, CHUNK):
    #    populaProduto(con, produtos)
    #    cont+=150
    #    populaCategoria(con, produtos)
    #    populaReview(con, produtos)
    #    print(f"inseriu {cont} produtos")

    #for produtos in parser(ARQUIVO, CHUNK):
    #    populaSimilar(con, produtos)
    #con.close()
        COPY_FROM_STDIN(produtos, "Product", "asin, title, prod_group, salesrank, total_review", con)
        #selectProduto(con)
    con.close()

main()