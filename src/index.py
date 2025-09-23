import psycopg
from parser import parser

SCHEMA = "sql/schema.sql"
CHUNK = 5
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
                if tabela == "Product":
                    asin = dado.get("ASIN")
                    title = dado.get("title", None)
                    prod_group = dado.get("group", None)
                    salesrank = dado.get("salesrank", None)
                    total_review = dado.get("review", None)
                    total_review = total_review['total'] if total_review else None
                    values = (asin,title,prod_group, salesrank, total_review)
                elif tabela == "Categories":
                    for categoria in dados.get("categories", None):
                        categoria = categoria.reverse().copy()
                        categoria.split("[")
                        # parte das categorias pra desenvolver

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

def main():
    con = conectar_postgres()
    ret = executar_script_sql(SCHEMA, con)
    if ret == 0:
        con = conectar_postgres()
    cont = 0

    for produtos in parser(ARQUIVO, CHUNK):
        COPY_FROM_STDIN(produtos, "Product", "asin, title, prod_group, salesrank, total_review", con)
    selectProduto(con)
    con.close()

main()