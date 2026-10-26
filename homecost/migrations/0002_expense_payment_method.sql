ALTER TABLE expenses ADD COLUMN payment_method VARCHAR;
UPDATE expenses SET payment_method = 'cash' WHERE payment_method IS NULL;
ALTER TABLE expenses ALTER COLUMN payment_method SET NOT NULL;
