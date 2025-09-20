import psycopg

def main():
    try:
        con = psycopg.connect(
            host="db",
            port=5432,
            dbname="ecommerce",
            user="postgres",
            password="postgres")
        print("tudo certinho '-'")
        con.close()
    except Exception as error:
        print("Deu erro ae: ", error)

import time

def count_lines(filepath: str):
    start = time.time()
    count = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for ff in f:
            count += 1
    elapsed = time.time() - start
    print(f"Linhas: {count}")
    print(f"Tempo: {elapsed:.2f} segundos")

count_lines("../data/amazon-meta.txt")
