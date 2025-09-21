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
SELECT Product.id_product, COUNT(Review.id_review) AS downloaded, AVG(Review.rating) AS avg_rating
FROM Product JOIN Review
ON Product.id_product = Review.id_product
GROUP BY Product.id_product
