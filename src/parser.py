# teste parser
import time


def mostraProdutos(produtos):
    print(f"Bloco de {len(produtos)} produtos")
    for produto in produtos:
        print(f" ID: {produto.get('Id', 'NULL')}")
        print(f" ASIN: {produto.get('ASIN', 'NULL')}")
        print(f" title: {produto.get('title', 'NULL')}")
        print(f" group: {produto.get('group', 'NULL')}")
        print(f" salesrank: {produto.get('salesrank', 'NULL')}")
        print(f" similar: {produto.get('similar', 'NULL')}")
        print(f" tem {produto.get('qnt_categorias', 0)} categorias:")
        if 'categories' in produto:
            cat = 1
            for categoria in produto['categories']:
                print(f" cat {cat}: - {categoria}")
                cat += 1
        print("----------")
        print(f" tem {len(produto['reviews'])} reviews:")
        for review in produto["reviews"]:
            print(f" - {review}")
        print()
    return produtos

def parser(arquivo, chunks):
    produtos = []
    produto = {}
    reviews_produto = []

    with open (arquivo, "r") as f:
        for linha in f:
            linha = linha.strip()

            if(linha.startswith("Id:")):
                #aq termina o produto antigo
                if produto:
                    produto["reviews"] = reviews_produto.copy()
                    reviews_produto = []
                    produtos.append(produto)
                    produto = {}
                    if len(produtos) >= chunks:
                        yield produtos
                        mostraProdutos(produtos)
                        produtos = []
                        break

                # novo produto
                produto = {
                    "Id":linha.split(":")[1].strip(),
                    "categories":[]
                }

            elif(linha.startswith("ASIN:")):
                produto["ASIN"] = linha.split(":")[1].strip()

            elif(linha.startswith("title:")):
                produto["title"] = linha.split(":",1)[1].strip()

            elif(linha.startswith("group:")):
                produto["group"] = linha.split(":")[1].strip()

            elif(linha.startswith("salesrank:")):
                produto["salesrank"] = linha.split(":")[1].strip()

            elif(linha.startswith("similar:")):
                produto["similar"] = linha.split(":")[1].strip()

            elif (linha.startswith("categories:")):
                produto["qnt_categorias"] = linha.split(" ")[1].strip()

            elif linha.startswith("|"):
                partes = linha.split("|")
                categories_hierarquia = []
                for parte in partes:
                    categorias_limpas = parte.strip()
                    if categorias_limpas:
                        categories_hierarquia.append(categorias_limpas)
                if 'categories' in produto:
                    produto["categories"].append(categories_hierarquia)

            elif(linha.startswith("reviews:")):
                linha = linha.split(" ")
                produto["total"] = linha[2].strip()
                produto["downloaded"] = linha[5].strip()
                produto['avg_rating'] = linha[7].strip()

            elif "cutomer" in linha and "helpful" in linha:
                partes = linha.split(" ")
                partes_limpas = []
                for p in partes:
                    if p:
                        partes_limpas.append(p)
                if partes_limpas:
                    review = {
                        "data": partes_limpas[0],
                        "customer": partes_limpas[2],
                        "rating": int(partes_limpas[4]),
                        "votes": int(partes_limpas[6]),
                        "helpful": int(partes_limpas[8]),
                    }
                    reviews_produto.append(review)

    #esse treco aq eh pra pegar o ultimo produto do arquivo
    if produto:
        produto["reviews"] = reviews_produto.copy()
        produtos.append(produto)
        #mostraProdutos(produtos)

def main(arquivo, chunks):
    start = time.time()
    parser(arquivo, chunks)
    end = time.time()
    print(f"Tempo de execucao do parse: {end - start}")
