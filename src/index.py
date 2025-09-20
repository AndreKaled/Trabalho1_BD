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
            if "reviews" in ff:
                dado = ff.split(' ')
                for i in range(len(dado)):
                    palavra = dado[i]
                    if "total:" == palavra:
                        i+=1
                        #print(dado[i-1], dado[i])
                        total = int(dado[i])
                        i+=3
                        #print("testeee")
                        #print(dado[i], i)

                        downloaded = int(dado[i])
                        if total != downloaded:
                            print("achou diferente aq")
                            print(dado)

    elapsed = time.time() - start
    print(f"Linhas: {count}")
    print(f"Tempo: {elapsed:.2f} segundos")


