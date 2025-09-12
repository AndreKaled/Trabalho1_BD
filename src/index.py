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

main()