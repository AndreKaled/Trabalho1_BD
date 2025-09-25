-- procedimento tecnico pra nao ter q dar restart no docker só pra testar
DROP VIEW  IF EXISTS View_review;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Product_categories;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Product_similar;
DROP TABLE IF EXISTS Product;

CREATE TABLE Product(
    id_product SERIAL,
    asin VARCHAR(20) UNIQUE,
    title VARCHAR(500),
    prod_group VARCHAR(300),
    salesrank INTEGER,
    total_review INTEGER,
    avg_rating FLOAT,
    PRIMARY KEY (id_product)
    
);

-- relacao de um produto com outros produtos
CREATE TABLE Product_similar(
    id_product INTEGER,
    asin_similar VARCHAR(20) ,
    PRIMARY KEY (id_product, asin_similar),
    FOREIGN KEY (id_product) REFERENCES Product(id_product),
    FOREIGN KEY (asin_similar) REFERENCES Product(asin)
);

-- categoria segue uma chamada recursiva até encontrar NULL
CREATE TABLE Categories(
    id_category INTEGER UNIQUE,
    category_name VARCHAR(100),
    id_category_father INTEGER DEFAULT NULL,
    PRIMARY KEY (id_category),
    FOREIGN KEY (id_category_father) REFERENCES Categories(id_category)
);

-- relacao de produto com categorias
CREATE TABLE Product_categories(
    id_product INTEGER,
    id_category_son INTEGER,
    PRIMARY KEY (id_product, id_category_son),
    FOREIGN KEY (id_product) REFERENCES Product(id_product),
    FOREIGN KEY (id_category_son) REFERENCES Categories(id_category)
);

CREATE TABLE Customer(
    id_customer VARCHAR(14) PRIMARY KEY
);

CREATE TABLE Review(
    id_review SERIAL,
    id_product INTEGER,
    date DATE,
    customer VARCHAR(20),
    rating INTEGER,
    votes INTEGER,
    helpful INTEGER,
    PRIMARY KEY (id_review),
    FOREIGN KEY (customer) REFERENCES Customer(id_customer),
    FOREIGN KEY (id_product) REFERENCES Product(id_product)
);

CREATE VIEW View_review AS
SELECT 
    p.id_product,
    COALESCE(Rev.review_count, 0) AS downloaded,
    COALESCE(Sim.similar_count, 0) AS num_similares,
    COALESCE(Cat.category_count, 0) AS num_categorias
FROM 
    Product AS p
LEFT JOIN (
    SELECT 
        id_product,
        COUNT(id.review) as review_count
    FROM
        Review
    GROUP BY
        id_product
) AS Rev ON p.id_product = Rev.id_product

LEFT JOIN (
    SELECT
        id_product,
        COUNT(id_category_son) AS category_count
    FROM 
        Product_categories
    GROUP BY
        id_product
) AS Cat ON p.id_product = Cat.id_product

LEFT JOIN (
    SELECT 
        id_product,
        COUNT(asin_similar) AS similar_count
    FROM 
        Product_similar
    GROUP BY
        id_product
) AS Sim ON p.id_product = Sim.id_product

