CREATE TABLE Product(
    id_product INTEGER SERIAL,
    asin VARCHAR(20) UNIQUE,
    title VARCHAR(50),
    prod_group VARCHAR(20),
    salesrank INTEGER,
    total INTEGER,
    PRIMARY KEY (id_product)
);

-- relacao de um produto com outros produtos
CREATE TABLE Product_similar(
    id_product INTEGER,
    id_similar INTEGER CHECK (id_similar != id_product),
    PRIMARY KEY (id_product, id_similar),
    FOREIGN KEY (id_product) REFERENCES Product(id_product),
    FOREIGN KEY (id_similar) REFERENCES Product(id_product),
);

-- categoria segue uma chamada recursiva até encontrar NULL
CREATE TABLE Categories(
    id_category INTEGER,
    category_name VARCHAR(50),
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

CREATE TABLE Review(
    id_review INTEGER SERIAL,
    id_product INTEGER,
    date DATE,
    customer VARCHAR(14),
    rating INTEGER,
    votes INTEGER,
    helpful INTEGER,
    PRIMARY KEY (id_review),
    FOREIGN KEY (customer) REFERENCES Customer(id_customer),
    FOREIGN KEY (id_product) REFERENCES Product(id_product)
);

CREATE TABLE Customer(
    id_customer VARCHAR(14) PRIMARY KEY,
);

CREATE VIEW View_review AS
SELECT Product.id_product, COUNT(Review.id_review) AS downloaded, AVG(Review.rating) AS avg_rating
FROM Product JOIN Review
ON Product.id_product = Review.id_product
GROUP BY Product.id_product
