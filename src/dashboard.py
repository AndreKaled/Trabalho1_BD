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
    "01_contagem_total_produtos": """
        SELECT COUNT(*) AS total_de_produtos FROM Product;
    """,

    "02_top_5_produtos_com_mais_reviews": """
        SELECT
            p.id_product,
            p.title,
            COALESCE(vr.downloaded, 0) AS quantidade_reviews
        FROM
            Product p
        LEFT JOIN
            View_review vr ON p.id_product = vr.id_product
        ORDER BY
            quantidade_reviews DESC 
        LIMIT 5;
    """,

    "03_quantidade_de_review": """
        SELECT COUNT(*)
        FROM Review
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