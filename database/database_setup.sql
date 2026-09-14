-- =========================================================================
-- MoMo SMS Data Processing System — Database Setup
-- Team Member: Person B (SQL Implementation)
-- Built from Person A's ERD (see ERD_diagram.html / ERD_source.mmd)
-- Target: MySQL 8.0+
-- =========================================================================

DROP DATABASE IF EXISTS momo_sms_system;
CREATE DATABASE momo_sms_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE momo_sms_system;

-- -------------------------------------------------------------------------
-- 1. Users  (senders / receivers of MoMo transactions)
-- -------------------------------------------------------------------------
CREATE TABLE Users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for each user/customer',
    first_name      VARCHAR(50)  NOT NULL COMMENT 'User first name',
    last_name       VARCHAR(50)  NOT NULL COMMENT 'User last name',
    phone_number    VARCHAR(15)  NOT NULL UNIQUE COMMENT 'MoMo registered phone number, e.g. 250788123456',
    national_id     VARCHAR(20)  DEFAULT NULL COMMENT 'National ID, optional, used for KYC',
    email           VARCHAR(100) DEFAULT NULL COMMENT 'Contact email address',
    user_type       ENUM('INDIVIDUAL','MERCHANT','AGENT') NOT NULL DEFAULT 'INDIVIDUAL'
                        COMMENT 'Classification of the account holder',
    account_status  ENUM('ACTIVE','SUSPENDED','CLOSED') NOT NULL DEFAULT 'ACTIVE'
                        COMMENT 'Current lifecycle status of the account',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_phone CHECK (phone_number REGEXP '^[0-9]{9,15}$')
) ENGINE=InnoDB COMMENT='Stores sender/receiver customer master data';

CREATE INDEX idx_users_phone   ON Users(phone_number);
CREATE INDEX idx_users_status  ON Users(account_status);

-- -------------------------------------------------------------------------
-- 2. Transaction_Categories  (lookup table)
-- -------------------------------------------------------------------------
CREATE TABLE Transaction_Categories (
    category_id     INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for the category',
    category_name   VARCHAR(50)  NOT NULL UNIQUE COMMENT 'e.g. DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT, AIRTIME',
    category_code   VARCHAR(10)  NOT NULL UNIQUE COMMENT 'Short code used during raw SMS parsing, e.g. DEP, WDR',
    description     VARCHAR(255) DEFAULT NULL COMMENT 'Human readable description',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether new transactions may use this category',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Lookup table for MoMo transaction/payment types';

CREATE INDEX idx_category_code ON Transaction_Categories(category_code);

-- -------------------------------------------------------------------------
-- 3. Transactions  (main fact table)
-- -------------------------------------------------------------------------
CREATE TABLE Transactions (
    transaction_id          INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for the transaction',
    transaction_reference   VARCHAR(30) NOT NULL UNIQUE COMMENT 'MoMo system reference/ID parsed from SMS',
    sender_id               INT DEFAULT NULL COMMENT 'FK to Users: who initiated the transaction',
    receiver_id             INT DEFAULT NULL COMMENT 'FK to Users: who received the funds',
    category_id             INT NOT NULL COMMENT 'FK to Transaction_Categories',
    amount                  DECIMAL(15,2) NOT NULL COMMENT 'Principal transaction amount',
    fee                     DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Fee charged for the transaction',
    balance_after           DECIMAL(15,2) DEFAULT NULL COMMENT 'Reported account balance after the transaction (from SMS)',
    currency                CHAR(3) NOT NULL DEFAULT 'RWF' COMMENT 'ISO 4217 currency code',
    transaction_date        DATETIME NOT NULL COMMENT 'Timestamp of the transaction, parsed from the SMS body',
    status                  ENUM('PENDING','COMPLETED','FAILED','REVERSED') NOT NULL DEFAULT 'COMPLETED'
                                 COMMENT 'Processing status of the transaction',
    raw_sms_body            TEXT DEFAULT NULL COMMENT 'Original unparsed SMS text, retained for audit/debugging',
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_sender
        FOREIGN KEY (sender_id) REFERENCES Users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_transactions_receiver
        FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id) REFERENCES Transaction_Categories(category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_txn_amount CHECK (amount > 0),
    CONSTRAINT chk_txn_fee    CHECK (fee >= 0)
) ENGINE=InnoDB COMMENT='Main table storing parsed MoMo transaction records';

CREATE INDEX idx_txn_date      ON Transactions(transaction_date);
CREATE INDEX idx_txn_sender    ON Transactions(sender_id);
CREATE INDEX idx_txn_receiver  ON Transactions(receiver_id);
CREATE INDEX idx_txn_category  ON Transactions(category_id);
CREATE INDEX idx_txn_status    ON Transactions(status);

-- -------------------------------------------------------------------------
-- 4. Tags  (supports the M:N relationship with Transactions)
-- -------------------------------------------------------------------------
CREATE TABLE Tags (
    tag_id          INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a tag',
    tag_name        VARCHAR(30) NOT NULL UNIQUE COMMENT 'e.g. HIGH_VALUE, SUSPICIOUS, RECURRING, DUPLICATE',
    tag_description VARCHAR(255) DEFAULT NULL COMMENT 'Explains when/why the tag is applied'
) ENGINE=InnoDB COMMENT='Reusable labels that can be attached to many transactions';

-- -------------------------------------------------------------------------
-- 5. Transaction_Tags  (junction table resolving the M:N relationship)
-- -------------------------------------------------------------------------
CREATE TABLE Transaction_Tags (
    transaction_id  INT NOT NULL COMMENT 'FK to Transactions',
    tag_id          INT NOT NULL COMMENT 'FK to Tags',
    tagged_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When the tag was applied',
    tagged_by       VARCHAR(50) NOT NULL DEFAULT 'SYSTEM' COMMENT 'Process or user who applied the tag',
    PRIMARY KEY (transaction_id, tag_id),
    CONSTRAINT fk_tt_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tt_tag
        FOREIGN KEY (tag_id) REFERENCES Tags(tag_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Junction table resolving the many-to-many relationship between Transactions and Tags';

-- -------------------------------------------------------------------------
-- 6. System_Logs  (pipeline processing audit trail)
-- -------------------------------------------------------------------------
CREATE TABLE System_Logs (
    log_id          INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for the log entry',
    transaction_id  INT DEFAULT NULL COMMENT 'FK to Transactions; NULL if not tied to a specific transaction (e.g. parse failure)',
    log_level       ENUM('INFO','WARNING','ERROR','DEBUG') NOT NULL DEFAULT 'INFO' COMMENT 'Severity level',
    process_stage   ENUM('XML_PARSING','VALIDATION','CATEGORIZATION','DB_INSERTION','EXPORT') NOT NULL
                        COMMENT 'Pipeline stage that generated this log entry',
    message         TEXT NOT NULL COMMENT 'Log message detail',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Tracks data processing pipeline events for auditing and debugging';

CREATE INDEX idx_logs_level    ON System_Logs(log_level);
CREATE INDEX idx_logs_stage    ON System_Logs(process_stage);
CREATE INDEX idx_logs_created  ON System_Logs(created_at);


-- =========================================================================
-- SAMPLE DATA (5+ records per main table)
-- =========================================================================

-- Users
INSERT INTO Users (first_name, last_name, phone_number, national_id, email, user_type, account_status) VALUES
('Aline',   'Uwimana',  '250788123456', '1198800123456789', 'aline.uwimana@example.com',  'INDIVIDUAL', 'ACTIVE'),
('Eric',    'Niyonzima','250788234567', '1198800234567890', 'eric.n@example.com',         'INDIVIDUAL', 'ACTIVE'),
('Grace',   'Mukamana', '250788345678', '1198800345678901', 'grace.mukamana@example.com', 'INDIVIDUAL', 'ACTIVE'),
('Jean Paul','Habimana','250788456789', NULL,               'jp.habimana@example.com',    'INDIVIDUAL', 'SUSPENDED'),
('QuickMart','Ltd',     '250788567890', NULL,               'billing@quickmart.rw',       'MERCHANT',   'ACTIVE'),
('Samuel',  'Ndayisenga','250788678901', '1198800678901234','samuel.nday@example.com',    'AGENT',      'ACTIVE');

-- Transaction_Categories
INSERT INTO Transaction_Categories (category_name, category_code, description, is_active) VALUES
('DEPOSIT',    'DEP', 'Cash deposited into a MoMo wallet',                 TRUE),
('WITHDRAWAL', 'WDR', 'Cash withdrawn from a MoMo wallet via agent',       TRUE),
('TRANSFER',   'TRF', 'Peer-to-peer transfer between two MoMo users',      TRUE),
('PAYMENT',    'PAY', 'Payment made to a merchant for goods/services',     TRUE),
('AIRTIME',    'AIR', 'Airtime/data bundle purchase',                     TRUE);

-- Transactions
INSERT INTO Transactions (transaction_reference, sender_id, receiver_id, category_id, amount, fee, balance_after, currency, transaction_date, status, raw_sms_body) VALUES
('MP240915.0930.A12345', NULL, 1, 1, 50000.00,   0.00, 52000.00, 'RWF', '2024-09-15 09:30:00', 'COMPLETED', 'You have received 50000 RWF. Your new balance: 52000 RWF.'),
('MP240915.1015.B23456', 1,    3, 3, 15000.00, 100.00, 36900.00, 'RWF', '2024-09-15 10:15:00', 'COMPLETED', 'You have sent 15000 RWF to Grace Mukamana. Fee: 100 RWF. New balance: 36900 RWF.'),
('MP240916.0800.C34567', 2,    NULL, 2, 20000.00, 200.00, 10500.00, 'RWF','2024-09-16 08:00:00', 'COMPLETED', 'You have withdrawn 20000 RWF via Agent Samuel. Fee: 200 RWF. New balance: 10500 RWF.'),
('MP240916.1230.D45678', 3,    5, 4, 8500.00,   50.00, 28350.00, 'RWF', '2024-09-16 12:30:00', 'COMPLETED', 'Payment of 8500 RWF to QuickMart Ltd successful. Fee: 50 RWF. New balance: 28350 RWF.'),
('MP240917.0900.E56789', 4,    NULL, 5, 2000.00,   0.00, 4300.00,  'RWF','2024-09-17 09:00:00', 'FAILED',    'Airtime purchase of 2000 RWF failed. Insufficient funds.'),
('MP240917.1500.F67890', 2,    1, 3, 30000.00,  150.00, 45500.00, 'RWF','2024-09-17 15:00:00', 'COMPLETED', 'You have sent 30000 RWF to Aline Uwimana. Fee: 150 RWF. New balance: 45500 RWF.');

-- Tags
INSERT INTO Tags (tag_name, tag_description) VALUES
('HIGH_VALUE',  'Transaction amount exceeds the high-value threshold (e.g. 25,000 RWF)'),
('SUSPICIOUS',  'Flagged by automated rules for manual review'),
('RECURRING',   'Part of a recurring/scheduled payment pattern'),
('FAILED_RETRY','A failed transaction that was subsequently retried'),
('MERCHANT_PAY','Payment made to a registered merchant account');

-- Transaction_Tags (junction rows — demonstrates the M:N relationship)
INSERT INTO Transaction_Tags (transaction_id, tag_id, tagged_by) VALUES
(1, 1, 'SYSTEM'),
(2, 3, 'SYSTEM'),
(4, 5, 'SYSTEM'),
(5, 4, 'SYSTEM'),
(6, 1, 'SYSTEM'),
(6, 2, 'analyst_grace');

-- System_Logs
INSERT INTO System_Logs (transaction_id, log_level, process_stage, message) VALUES
(1, 'INFO',    'XML_PARSING',    'Successfully parsed deposit SMS for reference MP240915.0930.A12345'),
(2, 'INFO',    'DB_INSERTION',   'Transfer transaction MP240915.1015.B23456 inserted successfully'),
(3, 'INFO',    'CATEGORIZATION', 'Withdrawal transaction categorized using code WDR'),
(5, 'ERROR',   'VALIDATION',     'Airtime transaction MP240917.0900.E56789 failed balance validation check'),
(NULL, 'WARNING', 'XML_PARSING', 'Skipped malformed SMS record at batch offset 4821 — missing timestamp field'),
(6, 'INFO',    'EXPORT',         'Transaction MP240917.1500.F67890 included in nightly export batch #204');


-- =========================================================================
-- SAMPLE CRUD OPERATIONS (for testing / documentation screenshots)
-- =========================================================================

-- CREATE: add a new user and a transaction referencing them
INSERT INTO Users (first_name, last_name, phone_number, user_type) VALUES ('Diane', 'Umutoni', '250788789012', 'INDIVIDUAL');
INSERT INTO Transactions (transaction_reference, sender_id, receiver_id, category_id, amount, fee, balance_after, currency, transaction_date, status)
VALUES ('MP240918.0900.G78901', 7, 3, 3, 5000.00, 50.00, 12300.00, 'RWF', '2024-09-18 09:00:00', 'COMPLETED');

-- READ: full transaction detail with joined sender/receiver/category names
SELECT
    t.transaction_reference,
    su.first_name AS sender_first, su.last_name AS sender_last,
    ru.first_name AS receiver_first, ru.last_name AS receiver_last,
    tc.category_name,
    t.amount, t.fee, t.status, t.transaction_date
FROM Transactions t
LEFT JOIN Users su ON t.sender_id = su.user_id
LEFT JOIN Users ru ON t.receiver_id = ru.user_id
JOIN Transaction_Categories tc ON t.category_id = tc.category_id
ORDER BY t.transaction_date DESC;

-- READ: all tags attached to a given transaction (demonstrates the M:N join)
SELECT tg.tag_name, tt.tagged_at, tt.tagged_by
FROM Transaction_Tags tt
JOIN Tags tg ON tt.tag_id = tg.tag_id
WHERE tt.transaction_id = 6;

-- UPDATE: mark a failed transaction as reversed after investigation
UPDATE Transactions
SET status = 'REVERSED'
WHERE transaction_reference = 'MP240917.0900.E56789';

-- UPDATE: suspend a user account
UPDATE Users SET account_status = 'SUSPENDED' WHERE phone_number = '250788789012';

-- DELETE: remove a tag assignment (does not delete the transaction or the tag itself)
DELETE FROM Transaction_Tags WHERE transaction_id = 5 AND tag_id = 4;

-- DELETE: demonstrate ON DELETE SET NULL — deleting a user does not orphan their past transactions
-- (sender_id/receiver_id become NULL instead of the row being removed)
DELETE FROM Users WHERE phone_number = '250788789012';
