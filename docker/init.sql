DROP SCHEMA IF EXISTS book_heaven CASCADE;

CREATE SCHEMA book_heaven;

SET search_path = "book_heaven";

CREATE TYPE rule_types AS ENUM ('c', 'a');

DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    username varchar(255) PRIMARY KEY,
    email varchar(255) CHECK ( regexp_like(email, '^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$') ),
    password varchar(255),
    name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    phone varchar(13) CHECK ( regexp_like(phone, '(^(0?9)|(\+?989))\d{9}$') ),
    rule rule_types
);

DROP TABLE IF EXISTS customer CASCADE;
CREATE TABLE customer (
    customer_id varchar(255) PRIMARY KEY,
    address TEXT,
    location point,
    FOREIGN KEY (customer_id)
                      REFERENCES users(username)
);

DROP TABLE IF EXISTS warehouse CASCADE;
CREATE TABLE warehouse (
    warehouse_id varchar(255) PRIMARY KEY,
    name varchar(255),
    address TEXT,
    location point
);

DROP TABLE IF EXISTS admin CASCADE;
CREATE TABLE admin (
    admin_id varchar(255) PRIMARY KEY,
    national_id char(10) UNIQUE,
    workplace varchar(255),
    salary numeric(10, 2),
    bank_account_number varchar(255),
    FOREIGN KEY (admin_id)
                   REFERENCES users(username),
    FOREIGN KEY (workplace)
                   REFERENCES warehouse(warehouse_id)
);

DROP TABLE IF EXISTS manager CASCADE;
CREATE TABLE manager (
    national_id char(10) PRIMARY KEY,
    email varchar(255) CHECK ( regexp_like(email, '^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$') ),
    password varchar(255),
    name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    phone varchar(13) CHECK ( regexp_like(phone, '(^(0?9)|(\+?989))\d{9}$') ),
    workplace varchar(255),
    salary numeric(10, 2),
    bank_account_number varchar(32),
    FOREIGN KEY (workplace)
                     REFERENCES warehouse(warehouse_id)
);

DROP TABLE IF EXISTS management_period CASCADE;
CREATE TABLE management_period (
    manager_id varchar(255),
    warehouse_manager varchar(255),
    from_date DATE,
    to_date DATE,
    FOREIGN KEY (manager_id)
                    REFERENCES manager(national_id),
    FOREIGN KEY (warehouse_manager)
                    REFERENCES warehouse(warehouse_id),
    PRIMARY KEY (manager_id, warehouse_manager, from_date)
);

CREATE DOMAIN isbn AS varchar(17) NOT NULL;

DROP TABLE IF EXISTS book CASCADE;
CREATE TABLE book (
    book_id isbn PRIMARY KEY,
    title varchar(255),
    price numeric(10, 2),
    author_name varchar(255),
    publisher varchar(255),
    edition varchar(32),
    year INT
);

DROP TABLE IF EXISTS order_list CASCADE;
CREATE TABLE order_list (
    order_id SERIAL PRIMARY KEY,
    customer_id varchar(255),
    warehouse_id varchar(255),
    FOREIGN KEY (customer_id)
                        REFERENCES customer(customer_id),
    FOREIGN KEY (warehouse_id)
                        REFERENCES warehouse(warehouse_id)
);

DROP TABLE IF EXISTS books_per_order CASCADE;
CREATE TABLE books_per_order (
    order_id INTEGER,
    book_id varchar(255),
    count int2,
    FOREIGN KEY (order_id)
                        REFERENCES order_list(order_id),
    FOREIGN KEY (book_id)
                        REFERENCES book(book_id),
    PRIMARY KEY (order_id, book_id)
);

DROP TABLE IF EXISTS inventory CASCADE;
CREATE TABLE inventory (
    warehouse_id varchar(255),
    book_id varchar(255),
    count INT,
    PRIMARY KEY (warehouse_id, book_id),
    FOREIGN KEY (warehouse_id)
                       REFERENCES warehouse(warehouse_id),
    FOREIGN KEY (book_id)
                       REFERENCES book(book_id)
);

DROP TABLE IF EXISTS comments CASCADE;
CREATE TABLE comments (
    comment_id SERIAL PRIMARY KEY,
    book_id isbn,
    user_id varchar(255),
    score INT CHECK (score BETWEEN 0 AND 10),
    content TEXT,
    updated_time TIMESTAMP DEFAULT current_timestamp,
    FOREIGN KEY (book_id)
                      REFERENCES book(book_id),
    FOREIGN KEY (user_id)
                      REFERENCES users(username),
    UNIQUE (book_id, user_id)
);

CREATE OR REPLACE FUNCTION degradation_admin_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
    BEGIN
        UPDATE users u
        SET rule = 'c'
        WHERE u.username = OLD.admin_id;
        RETURN OLD;
    END;
$$;

DROP TRIGGER IF EXISTS degradation_admin ON admin;
CREATE TRIGGER degradation_admin
    BEFORE DELETE
    ON admin
    FOR EACH ROW
    EXECUTE PROCEDURE degradation_admin_func();

CREATE OR REPLACE FUNCTION check_admin_degree_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
    BEGIN
        IF 'a' != (
            SELECT u.rule
            FROM users u
            WHERE u.username = NEW.admin_id)
        THEN
            RAISE SQLSTATE '22023' USING MESSAGE = 'User rule should be admin (a)';
        ELSE
            RETURN NEW;
        END IF;
    END;
$$;

DROP TRIGGER IF EXISTS check_admin_degree ON admin;
CREATE TRIGGER check_admin_degree
    BEFORE INSERT
    ON admin
    FOR EACH ROW
    EXECUTE PROCEDURE check_admin_degree_func();

DROP VIEW IF EXISTS orders;
CREATE VIEW orders
AS
    SELECT customer_id, ol.order_id, title, price, bpo.count, author_name
    FROM order_list ol
    JOIN book_heaven.books_per_order bpo ON ol.order_id = bpo.order_id
    JOIN book_heaven.book b ON bpo.book_id = b.book_id;


----------------------------------------------------------------------------------


INSERT INTO warehouse (
    warehouse_id, name, address, location
) VALUES
(
    'tehran_001',
    'انبار مرکزی تهران',
    'تهران، خیابان انقلاب، خیابان دانشگاه',
    point(51.3982989, 35.7008161)
),
(
    'shiraz_001',
    'انبار شیراز',
    'شیراز، خیابان ملاصدرا',
    point(52.5188579, 29.6278063)
);

INSERT INTO users (
    username, email, password, name, last_name, phone, rule
) VALUES
(
    'ali_rezaei',
    'ali.rezaei@gmail.com',
    '1234',
    'علی',
    'رضایی',
    '09351234567',
    'c'
),
(
    'sara_mohammadi',
    'sara.mohammadi@gmail.com',
    '1234',
    'سارا',
    'محمدی',
    '09121234567',
    'c'
),
(
    'reza_karimi',
    'reza.karimi@gmail.com',
    '1234',
    'رضا',
    'کریمی',
    '09125551234',
    'a'
);

INSERT INTO customer (
    customer_id, address, location
) VALUES
(
    'ali_rezaei',
    'تهران، خیابان ولیعصر، خیابان فلاحی',
    point(51.4199901, 35.8048881)
),
(
    'sara_mohammadi',
    'شیراز، خیابان قصردشت، کوچه دوم',
    point(52.5277414, 29.620537)
);

INSERT INTO admin (
    admin_id, national_id, workplace, salary, bank_account_number
) VALUES
(
    'reza_karimi',
    '0878721963',
    'tehran_001',
    35000000.00,
    '6037997128845729'
);

INSERT INTO manager (
    national_id, email, password, name, last_name,
    phone, workplace, salary, bank_account_number
) VALUES
(
    '0125782678',
    'mohsen.hosseini@gmail.com',
    '1234',
    'محسن',
    'حسینی',
    '09123234795',
    'tehran_001',
    50000000.00,
    '6037997126355689'
),
(
    '0225481185',
    'maryam.ahmadi@gmail.com',
    '1234',
    'مریم',
    'احمدی',
    '09127754270',
    'shiraz_001',
    45000000.00,
    '6037835463728912'
);

INSERT INTO management_period (
    manager_id, warehouse_manager, from_date, to_date
) VALUES
(
    '0125782678',
    'tehran_001',
    DATE '2024-01-01',
    NULL
),
(
    '0225481185',
    'shiraz_001',
    DATE '2024-03-01',
    NULL
);

INSERT INTO book (
    book_id, title, price, author_name, publisher, edition, year
) VALUES
(
    '9780735211292',
    'عادت‌های اتمی',
    450000.00,
    'جیمز کلیر',
    'نشر نوین',
    'اول',
    2018
),
(
    '9781455586691',
    'کار عمیق',
    380000.00,
    'کال نیوپورت',
    'نشر نوین',
    'اول',
    2016
),
(
    '9780374533557',
    'تفکر، سریع و کند',
    520000.00,
    'دنیل کانمن',
    'نشر نوین',
    'اول',
    2011
),
(
    '9780525559474',
    'کتابخانه نیمه‌شب',
    410000.00,
    'مت هیگ',
    'کتاب کوله پشتی',
    'اول',
    2020
);

INSERT INTO inventory (
    warehouse_id, book_id, count
) VALUES
('tehran_001', '9780735211292', 25),
('tehran_001', '9781455586691', 18),
('tehran_001', '9780374533557', 12),
('tehran_001', '9780525559474', 20),
('shiraz_001', '9780735211292', 10),
('shiraz_001', '9781455586691', 15),
('shiraz_001', '9780374533557', 8),
('shiraz_001', '9780525559474', 14);

INSERT INTO order_list (
    customer_id, warehouse_id
) VALUES
('ali_rezaei', 'tehran_001'),
('sara_mohammadi', 'shiraz_001'),
('ali_rezaei', 'tehran_001');

INSERT INTO books_per_order (
    order_id, book_id, count
) VALUES
(1, '9780735211292', 1),
(1, '9781455586691', 2),
(2, '9780525559474', 1),
(2, '9780374533557', 1),
(3, '9780735211292', 1),
(3, '9780525559474', 2);

INSERT INTO comments (
    book_id, user_id, score, content
) VALUES
(
    '9780735211292',
    'ali_rezaei',
    9,
    'کتاب بسیار کاربردی و مفیدی است. مثال‌های آن به درک بهتر عادت‌سازی کمک می‌کنند.'
),
(
    '9781455586691',
    'ali_rezaei',
    8,
    'برای یادگیری تمرکز عمیق و کاهش حواس‌پرتی بسیار مفید است.'
),
(
    '9780525559474',
    'sara_mohammadi',
    10,
    'داستانی جذاب و تأثیرگذار درباره انتخاب‌ها و فرصت‌های زندگی.'
),
(
    '9780374533557',
    'sara_mohammadi',
    9,
    'کتابی ارزشمند برای شناخت بهتر تصمیم‌گیری و خطاهای شناختی.'
),
(
    '9780735211292',
    'sara_mohammadi',
    8,
    'مطالب خوبی درباره ایجاد تغییرات کوچک و پایدار دارد.'
);
