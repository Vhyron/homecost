ALTER TABLE categories ADD COLUMN monthly_bill_expected BOOLEAN;
UPDATE categories SET monthly_bill_expected = FALSE WHERE monthly_bill_expected IS NULL;
UPDATE categories SET monthly_bill_expected = TRUE WHERE name IN ('electricity', 'water', 'wi-fi');
