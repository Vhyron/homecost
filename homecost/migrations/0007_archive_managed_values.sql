ALTER TABLE categories ADD COLUMN is_active BOOLEAN;
ALTER TABLE vendors ADD COLUMN is_active BOOLEAN;
ALTER TABLE payment_methods ADD COLUMN is_active BOOLEAN;
UPDATE categories SET is_active = TRUE;
UPDATE vendors SET is_active = TRUE;
UPDATE payment_methods SET is_active = TRUE;
