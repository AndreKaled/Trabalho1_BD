import sys
import os
import argparse
import csv
import psycopg # Biblioteca moderna para PostgreSQL. Se usar a mais antiga, use 'import psycopg2'

# ====================================================================
# SEÇÃO 6: DEFINIÇÃO DAS CONSULTAS SQL
#
# Substitua as strings abaixo pelas consultas reais do seu projeto.
# A chave do dicionário será usada como nome do arquivo CSV.
# ====================================================================
QUERIES = {
        "01_5_MAIS_UTEIS_MAIS_MENOS_AVALIACAO":
        """
        -- =======================================================================
        -- VERSÃO APRIMORADA: Garante a ordem dos grupos no resultado final
        -- =======================================================================

        WITH top_best_reviews AS (
            SELECT
                id_review, rating, helpful, votes, customer, data_review
            FROM Review
            WHERE id_product = (SELECT id_product FROM Product WHERE asin = '1559362022')
            ORDER BY rating DESC, helpful DESC
            LIMIT 5
        ),
        top_helpful_low_rated_reviews AS (
            SELECT
                id_review, rating, helpful, votes, customer, data_review
            FROM Review
            WHERE id_product = (SELECT id_product FROM Product WHERE asin = '1559362022')
            AND id_review NOT IN (SELECT id_review FROM top_best_reviews)
            ORDER BY rating DESC, helpful ASC
            LIMIT 5
        )
        -- Seleção final para juntar e ordenar os resultados
        SELECT
            categoria,
            rating,
            helpful,
            customer,
            data_review
        FROM (
            -- Primeiro grupo com chave de ordenação = 1
            SELECT
                1 AS sort_key,
                'Mais Úteis e com Maior Avaliação' AS categoria,
                rating, helpful, customer, data_review
            FROM
                top_best_reviews
            UNION ALL
            -- Segundo grupo com chave de ordenação = 2
            SELECT
                2 AS sort_key,
                'Mais Úteis e com Menor Avaliação' AS categoria,
                rating, helpful, customer, data_review
            FROM
                top_helpful_low_rated_reviews
        ) AS final_result
        ORDER BY
            sort_key; -- Ordena pela chave para garantir a separação dos blocos
            """,
        "02_SIMILARES_MAIORES_VENDAS(SALESRANK)":
        """
                -- Substitua '0790747324' pelo ASIN do produto que você deseja consultar
        SELECT
            p_sim.asin,
            p_sim.title,
            p_sim.salesrank AS similar_salesrank,
            p_orig.salesrank AS original_salesrank
        FROM
            Product AS p_orig
        JOIN
            Product_similar AS ps ON p_orig.id_product = ps.id_product
        JOIN
            Product AS p_sim ON ps.asin_similar = p_sim.asin
        WHERE
            p_orig.asin = 'B000002T4S'
            AND p_sim.salesrank < p_orig.salesrank
            AND p_sim.salesrank IS NOT NULL -- Boa prática para garantir que estamos comparando valores
        ORDER BY
            p_sim.salesrank ASC; -- Ordena para mostrar o melhor ranking primeiro
                            
        """,

        "03_EVOLUCAO_DIARIA":
        """
        SELECT DISTINCT ON (r.data_review)
            r.data_review AS dia_da_avaliacao,
            p.title AS titulo_do_produto,
            -- A função de janela calcula a média de todas as notas
            -- desde a primeira avaliação até a linha (dia) atual.
            AVG(r.rating) OVER (ORDER BY r.data_review ASC) AS media_acumulada
        FROM
            Review AS r
            JOIN
            Product AS p ON r.id_product = p.id_product
        WHERE
            p.asin = '1559362022'
        ORDER BY
            r.data_review ASC;
        """,


        "04_LIDERES_VENDAS_POR_GRUPO":"""
            WITH RankedProducts AS (
            -- Passo 1: Classificar cada produto dentro do seu grupo de produtos
            SELECT
                asin,
                title,
                prod_group,
                salesrank,
                ROW_NUMBER() OVER (PARTITION BY prod_group ORDER BY salesrank ASC) AS rank_in_group
            FROM
                Product
            WHERE
                salesrank IS NOT NULL AND salesrank > 0 -- Garante que estamos classificando apenas produtos com um ranking de vendas válido
        )
        -- Passo 2: Filtrar o resultado para obter apenas os 10 primeiros de cada grupo
        SELECT
            prod_group AS "Grupo de Produtos",
            rank_in_group AS "Rank no Grupo",
            asin,
            title AS "Título",
            salesrank AS "Rank de Vendas"
        FROM
            RankedProducts
        WHERE
            rank_in_group <= 10
        ORDER BY
            "Grupo de Produtos" ASC,
            "Rank no Grupo" ASC;
        """,

        "05_10_PRODUTOS_MAIOR_MEDIA_AVALICAO_UTEIS_POSITIVA":
        """
                    SELECT
            p.asin,
            p.title,
            AVG(
                CASE
                    WHEN (CAST(r.helpful AS NUMERIC) / r.votes) > 0.5 THEN 1.0
                    ELSE 0.0
                END
            ) AS percentual_avaliacoes_uteis
        FROM
            Product AS p
        JOIN
            Review AS r ON p.id_product = r.id_product
        WHERE
            r.votes > 0 -- Garante que a avaliação foi votada e evita divisão por zero
        GROUP BY
            p.asin,
            p.title
        ORDER BY
            percentual_avaliacoes_uteis DESC
        LIMIT 10; 
        """,
        
        "06_5_CATEGORIAS_MAIOR_MEDIA":
        """
                    SELECT
            c.category_name,
            AVG(
                CASE
                    WHEN (CAST(r.helpful AS NUMERIC) / r.votes) > 0.5 THEN 1.0
                    ELSE 0.0
                END
            ) AS percentual_avaliacoes_uteis
        FROM
            Categories AS c
        JOIN
            Product_categories AS pc ON c.id_category = pc.id_category_son
        JOIN
            Product AS p ON pc.id_product = p.id_product
        JOIN
            Review AS r ON p.id_product = r.id_product
        WHERE
            r.votes > 0 -- Garante que a avaliação foi votada e evita divisão por zero
        GROUP BY
            c.id_category,
            c.category_name
        ORDER BY
            percentual_avaliacoes_uteis DESC
        LIMIT 5;
        """,

        "07_10_CLIENTES_MAIS_COMENTARIOS_POR_GRUPO":
        """
                WITH RankedCustomers AS (
            SELECT
                r.customer,
                p.prod_group,
                COUNT(r.id_review) AS total_comentarios,
                ROW_NUMBER() OVER(PARTITION BY p.prod_group ORDER BY COUNT(r.id_review) DESC) AS ranking
            FROM
                Review AS r
            JOIN
                Product AS p ON r.id_product = p.id_product
            GROUP BY
                p.prod_group,
                r.customer
        )
        SELECT
            prod_group,
            customer,
            total_comentarios,
            ranking
        FROM
            RankedCustomers
        WHERE
            ranking <= 10
        ORDER BY
            prod_group,
            ranking;
        """
}


def execute_queries(db_params, output_dir):

    """
    Conecta ao banco de dados e executa as consultas definidas no dicionário QUERIES.
    """
    conn = None
    try:
        # Constrói a string de conexão (DSN)
        dsn = (
            f"host={db_params['host']} port={db_params['port']} "
            f"dbname={db_params['dbname']} user={db_params['user']} "
            f"password={db_params['password']}"
        )
        print("Conectando ao banco de dados PostgreSQL...")
        
        # O 'with' garante que a conexão será fechada automaticamente
        with psycopg.connect(dsn) as conn:
            # O 'with' garante que o cursor será fechado
            with conn.cursor() as cur:
                print("Conexão bem-sucedida.\n")

                # Cria o diretório de saída se ele não existir // ATENÇÃO PODE SER QUE DEVERA SER EXCLUÍDO
                os.makedirs(output_dir, exist_ok=True)

                # Itera sobre cada consulta definida
                for filename, sql_query in QUERIES.items():
                    print(f"--- Executando Consulta: {filename} ---")
                    
                    try:
                        cur.execute(sql_query)
                        results = cur.fetchall()
                        
                        # Pega os nomes das colunas a partir da descrição do cursor
                        colnames = [desc[0] for desc in cur.description]

                        # 1. Imprime a saída legível em STDOUT
                        print("Resultado:")
                        print(" | ".join(colnames))
                        print("-" * (sum(len(c) for c in colnames) + len(colnames) * 3))
                        for row in results:
                            print(" | ".join(map(str, row)))
                        
                        # 2. Salva o resultado em um arquivo CSV
                        csv_path = os.path.join(output_dir, f"{filename}.csv")
                        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                            csv_writer = csv.writer(csvfile)
                            csv_writer.writerow(colnames)  # Escreve o cabeçalho
                            csv_writer.writerows(results)  # Escreve os dados
                        
                        print(f"-> Resultado salvo em: {csv_path}\n")

                    except (psycopg.Error) as query_error:
                        print(f"!! Erro ao executar a consulta '{filename}': {query_error}", file=sys.stderr)
                        # Continua para a próxima consulta em vez de parar o script
    
    except (psycopg.OperationalError) as conn_error:
        print(f"!! ERRO DE CONEXÃO: Não foi possível conectar ao banco de dados.", file=sys.stderr)
        print(f"   Detalhes: {conn_error}", file=sys.stderr)
        # Retorna False em caso de falha na conexão
        return False
        
    except Exception as e:
        print(f"!! Um erro inesperado ocorreu: {e}", file=sys.stderr)
        return False
        
    # Retorna True em caso de sucesso na execução
    return True

def main():
    """
    Função principal que analisa os argumentos e chama a execução das consultas.
    """
    # ====================================================================
    # SEÇÃO 5: PARÂMETROS DE EXECUÇÃO
    # ====================================================================
    parser = argparse.ArgumentParser(description="Script para executar consultas SQL em um banco de dados PostgreSQL.")
    
    # Usa variáveis de ambiente como fallback para os parâmetros, o que é uma boa prática
    parser.add_argument('--db-host', default=os.getenv('PGHOST', 'db'), help='Host do banco de dados.')
    parser.add_argument('--db-port', default=os.getenv('PGPORT', '5432'), help='Porta do banco de dados.')
    parser.add_argument('--db-name', default=os.getenv('POSTGRES_DB', 'ecommerce'), help='Nome do banco de dados.')
    parser.add_argument('--db-user', default=os.getenv('POSTGRES_USER', 'postgres'), help='Usuário do banco de dados.')
    parser.add_argument('--db-password', default=os.getenv('POSTGRES_PASSWORD'), required=os.getenv('POSTGRES_PASSWORD') is None, help='Senha do banco de dados.')
    parser.add_argument('--output-dir', default='/app/out', help='Diretório para salvar os arquivos CSV.')
    parser.add_argument(
        '--product-asin',
        type=str,
        default=None, # Valor padrão é None, indicando que não foi fornecido
        help='ASIN (Identificador) do produto para consultas que exigem um produto específico.'
    )
    args = parser.parse_args()

    product_asin = args.product_asin

    db_params = {
        'host': args.db_host,
        'port': args.db_port,
        'dbname': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }

    if execute_queries(db_params, args.output_dir):
        print("Todas as consultas foram executadas com sucesso.")
        sys.exit(0) # Termina com código 0 em sucesso
    else:
        print("Ocorreram erros durante a execução.")
        sys.exit(1) # Termina com código 1 em caso de falha

if __name__ == "__main__":
    main()