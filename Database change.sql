-- SQLite
-- 1. Backup current users table (optional, for safety)
CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;

-- 2. Add new columns to the users table
ALTER TABLE users ADD COLUMN department TEXT;
ALTER TABLE users ADD COLUMN job_title TEXT;
ALTER TABLE users ADD COLUMN phone_number TEXT;
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users ADD COLUMN salary REAL;
ALTER TABLE users ADD COLUMN cv_filename TEXT;
ALTER TABLE users ADD COLUMN upload_time TIMESTAMP;

-- 3. Migrate data from other tables into the users table

-- Migrate employee directory data
UPDATE users
SET
    department = (SELECT department FROM employee_directory WHERE employee_directory.user_id = users.id),
    job_title = (SELECT job_title FROM employee_directory WHERE employee_directory.user_id = users.id),
    phone_number = (SELECT phone_number FROM employee_directory WHERE employee_directory.user_id = users.id),
    address = (SELECT address FROM employee_directory WHERE employee_directory.user_id = users.id)
WHERE EXISTS (SELECT 1 FROM employee_directory WHERE employee_directory.user_id = users.id);

-- Migrate payroll data
UPDATE users
SET
    salary = (SELECT salary FROM payroll WHERE payroll.user_id = users.id)
WHERE EXISTS (SELECT 1 FROM payroll WHERE payroll.user_id = users.id);

-- Migrate upload data (CV files)
UPDATE users
SET
    cv_filename = (SELECT filename FROM uploads WHERE uploads.user_id = users.id),
    upload_time = (SELECT upload_time FROM uploads WHERE uploads.user_id = users.id)
WHERE EXISTS (SELECT 1 FROM uploads WHERE uploads.user_id = users.id);

-- 4. Drop the old tables (optional, only after verifying migration)
DROP TABLE IF EXISTS employee_directory;
DROP TABLE IF EXISTS payroll;
DROP TABLE IF EXISTS uploads;

-- 5. Verify the data migration
SELECT * FROM users;
