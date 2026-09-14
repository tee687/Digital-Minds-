 Digital-Minds
 Group Members
-Tendai Mtakiwa 
-Tasnim Maulidi 
-Asiegbunam Chidera 

 Project Board
Our Scrum board: [https://trello.com/invite/b/6a9e09ca5e9858c548a806a0/ATTI21ee3181734795623416aba49912382129EAE12F/scrum-board-digital-minds]


 MoMo SMS Transaction Database

Database Implementation

The full implementation is in [`database/database_setup.sql`](./database/database_setup.sql), built for MySQL, and includes:

- DDL statements creating all five tables with appropriate data types (`INT`, `VARCHAR`, `DECIMAL`, `DATETIME`)
- Referential integrity via `FOREIGN KEY` constraints on all relationships
- CHECK constraintson account type, transaction amount, transaction status, and log status
- Indexes on foreign keys, phone number, transaction date, and transaction status for query performance
- Column-level comments documenting the purpose of every field
- Sample data — 6 records inserted per main table, using realistic Rwandan MoMo user data
- CRUD operation tests — a working CREATE, READ (with joins), UPDATE, and DELETE example at the end of the script

Running the Script

1. Open the script in MySQL Workbench (or your preferred MySQL client)
2. Run the full script — it will create the `momo_transaction_db` database, all tables, sample data, and run the CRUD test queries
3. Use the Schemas panel to browse the created tables and verify the sample data

SQL to JSON Data Mapping

This section documents how the relational schema (MySQL) maps directly to the API payload structures (JSON).

| SQL Entity / Table | SQL Column(s) | JSON Field | JSON Data Type | Transformation & Mapping Rules |
| :--- | :--- | :--- | :--- | :--- |
| `Users` | `user_id` | `user_id` | Number (Integer) | Direct 1:1 primary key mapping. |
| `Users` | `first_name`, `last_name` | `first_name`, `last_name` | String | Direct 1:1 text mapping. |
| `Users` | `phone_number` | `phone_number` | String | Preserves leading digits and international format. |
| `Users` | `user_type`, `account_status` | `user_type`, `account_status` | String | SQL `ENUM` values mapped directly as uppercase JSON strings. |
| `Transaction_Categories` | `category_id`, `category_name` | `category_id`, `category_name` | Integer, String | Direct lookup table field mapping. |
| `Transactions` | `transaction_id`, `transaction_reference` | `transaction_id`, `transaction_reference` | Integer, String | Direct 1:1 transaction identifier mapping. |
| `Transactions` | `amount`, `fee`, `balance_after` | `amount`, `fee`, `balance_after` | Number (Float) | SQL `DECIMAL(15,2)` converted to JSON numeric floating point. |
| `Transactions` | `transaction_date` | `transaction_date` | String | SQL `DATETIME` converted to standard ISO 8601 UTC timestamp format (`YYYY-MM-DDTHH:MM:SSZ`). |
| `Transactions` $\rightarrow$ `Users` | `sender_id` (FK) | `sender` | Object | Foreign Key resolved into a nested `User` entity object containing sender metadata. |
| `Transactions` $\rightarrow$ `Users` | `receiver_id` (FK) | `receiver` | Object | Foreign Key resolved into a nested `User` entity object containing receiver metadata. |
| `Transactions` $\rightarrow$ `Transaction_Categories` | `category_id` (FK) | `category` | Object | Foreign Key resolved into a nested `Category` entity object. |
| `Transaction_Tags` | `transaction_id`, `tag_id` (M:N) | `tags` | Array of Objects | Junction table normalized into an array of embedded `Tag` objects attached to the transaction payload. |
| `System_Logs` | `transaction_id` (1:M) | `logs` | Array of Objects | 1:M relationship nested as an array of processing event objects. |

### Structural & Relational Mapping Strategy

1. **Foreign Key De-normalization:** In the relational database, tables use integer Foreign Keys (`sender_id`, `receiver_id`, `category_id`) to minimize redundancy. In the JSON API representation, these keys are expanded into nested child objects to provide complete context in a single payload.
2. **Relationship Serialization:**
   * **1:M (Transactions to Logs):** Represented as an embedded JSON array (`"logs": [...]`) containing all log entries associated with the transaction.
   * **M:N (Transactions to Tags):** The `Transaction_Tags` junction table is flattened into an embedded array of tag objects (`"tags": [...]`) inside the transaction JSON.
3. **Data Type Conversions:**
   * SQL `DATETIME` $\rightarrow$ JSON ISO 8601 String (`"2024-09-15T10:15:00Z"`).
   * SQL `DECIMAL` $\rightarrow$ JSON Number (`15000.00`).
   * SQL `ENUM` $\rightarrow$ JSON String (`"INDIVIDUAL"`, `"ACTIVE"`).
   * SQL `BOOLEAN` $\rightarrow$ JSON Native Boolean (`true`/`false`).




## System Architecture

![High-Level System Architecture](./Architecture%20.drawio.png)
