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



## System Architecture

![High-Level System Architecture](./Architecture%20.drawio.png)
