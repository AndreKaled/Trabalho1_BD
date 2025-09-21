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
        print(f"inserindo {len(total_categorias_inseridas)} categorias da tabela Categoria")
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

def main():
    con = conectar_postgres()
    ret = executar_script_sql(SCHEMA, con)
    if ret == 0:
        con = conectar_postgres()
    for produto in parser(ARQUIVO, CHUNK):
        populaProduto(con, produto)
        populaCategoria(con, produto)
    selectProduto(con)
    con.close()

main()