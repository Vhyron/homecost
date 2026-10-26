CREATE SEQUENCE expense_id_seq START 1;
CREATE TABLE expenses (
    id BIGINT PRIMARY KEY DEFAULT nextval('expense_id_seq'),
    paid_date DATE NOT NULL,
    category VARCHAR NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    vendor VARCHAR,
    cost_month DATE NOT NULL,
    bill_date DATE
);
CREATE TABLE categories (name VARCHAR PRIMARY KEY, unit VARCHAR);
CREATE TABLE vendors (name VARCHAR PRIMARY KEY);
CREATE TABLE payment_methods (name VARCHAR PRIMARY KEY);
