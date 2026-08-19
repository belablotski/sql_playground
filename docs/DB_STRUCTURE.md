# Database Structure & Sample Data

This document describes the schema and generated test data used in this
SQL playground. The primary dialect targeted is **Microsoft SQL Server
(T-SQL)** — see [`sql/schema.sql`](../sql/schema.sql) — with a SQLite
variant provided purely for convenience so the playground can be exercised
without a SQL Server instance (see [`scripts/build_sqlite_db.py`](../scripts/build_sqlite_db.py)).

## Domain

The database models a small retail / e-commerce store: customers place
orders, which are handled by employees, and each order consists of one or
more line items referencing products that belong to categories.

## Entity-Relationship Overview

```
Categories 1───* Products 1───* OrderItems *───1 Orders *───1 Customers
                                                   Orders *───1 Employees
                                                 Employees 1───* Employees (self, ManagerID)
```

## Tables

### `Customers`
Registered store customers.

| Column          | Type            | Notes                              |
|-----------------|-----------------|-------------------------------------|
| CustomerID      | INT IDENTITY PK | Surrogate key                      |
| FirstName       | NVARCHAR(50)    |                                     |
| LastName        | NVARCHAR(50)    |                                     |
| Email           | NVARCHAR(100)   | Unique                              |
| Phone           | NVARCHAR(25)    | Nullable                           |
| City            | NVARCHAR(50)    | Nullable                           |
| Country         | NVARCHAR(50)    | Nullable                           |
| RegisteredDate  | DATE            | Defaults to current date           |

### `Employees`
Store staff who process orders. Self-referencing via `ManagerID` to model
a simple reporting hierarchy (useful for recursive CTE / self-join
examples).

| Column      | Type            | Notes                                   |
|-------------|-----------------|------------------------------------------|
| EmployeeID  | INT IDENTITY PK |                                          |
| FirstName   | NVARCHAR(50)    |                                          |
| LastName    | NVARCHAR(50)    |                                          |
| Title       | NVARCHAR(50)    | e.g. "Sales Manager", "Support Agent"   |
| HireDate    | DATE            |                                          |
| ManagerID   | INT NULL        | FK to `Employees.EmployeeID`, self-join |

### `Categories`
Product categories (Electronics, Books, etc.).

| Column       | Type          | Notes            |
|--------------|---------------|------------------|
| CategoryID   | INT IDENTITY PK |                |
| CategoryName | NVARCHAR(50)  | Unique           |
| Description  | NVARCHAR(255) | Nullable         |

### `Products`
Items for sale.

| Column        | Type            | Notes                                |
|---------------|-----------------|----------------------------------------|
| ProductID     | INT IDENTITY PK |                                        |
| ProductName   | NVARCHAR(100)   |                                        |
| CategoryID    | INT             | FK to `Categories.CategoryID`         |
| UnitPrice     | DECIMAL(10,2)   | >= 0                                   |
| UnitsInStock  | INT             | >= 0, default 0                       |
| Discontinued  | BIT             | default 0                             |

### `Orders`
Customer orders.

| Column      | Type          | Notes                                              |
|-------------|---------------|------------------------------------------------------|
| OrderID     | INT IDENTITY PK |                                                    |
| CustomerID  | INT           | FK to `Customers.CustomerID`                        |
| EmployeeID  | INT           | FK to `Employees.EmployeeID`                        |
| OrderDate   | DATETIME2     |                                                      |
| ShipDate    | DATETIME2     | Nullable (null until shipped)                       |
| Status      | NVARCHAR(20)  | One of `Pending`, `Shipped`, `Delivered`, `Cancelled` |

### `OrderItems`
Line items belonging to an order (many-to-many between `Orders` and
`Products`).

| Column       | Type          | Notes                                              |
|--------------|---------------|------------------------------------------------------|
| OrderItemID  | INT IDENTITY PK |                                                    |
| OrderID      | INT           | FK to `Orders.OrderID`                              |
| ProductID    | INT           | FK to `Products.ProductID`                          |
| Quantity     | INT           | > 0                                                  |
| UnitPrice    | DECIMAL(10,2) | Price at time of order (>= 0)                        |
| Discount     | DECIMAL(4,3)  | Fraction between 0 and 1                             |
| LineTotal    | DECIMAL(12,2) | Computed, persisted: `Quantity * UnitPrice * (1 - Discount)` |

## Generated Test Data

Data is synthetically generated with [Faker](https://faker.readthedocs.io/)
via [`scripts/generate_data.py`](../scripts/generate_data.py). By default
it creates (seed `42`, deterministic/reproducible):

| Table        | Default row count |
|--------------|--------------------|
| Categories   | 10                 |
| Customers    | 100                |
| Employees    | 8                  |
| Products     | 60                 |
| Orders       | 400                |
| OrderItems   | ~1,200 (1–5 per order) |

Notes on the generated data:
- `Employees` form a simple hierarchy: employee 1 has no manager; every
  later employee reports to a randomly chosen earlier employee.
- `Orders.Status` is weighted: Pending 15%, Shipped 25%, Delivered 55%,
  Cancelled 5%. `ShipDate` is only populated for `Shipped`/`Delivered` orders.
- `OrderItems.Discount` is mostly `0`, occasionally `0.05`–`0.2`.
- Row counts, and the random seed, are configurable via CLI arguments.

## Files

| Path                              | Purpose                                                    |
|------------------------------------|-------------------------------------------------------------|
| `sql/schema.sql`                  | T-SQL DDL for SQL Server (source of truth for the schema)   |
| `sql/sample_queries.sql`          | Example queries: joins, aggregates, window functions, CTEs |
| `scripts/generate_data.py`        | Generates CSV files and a T-SQL insert script               |
| `scripts/build_sqlite_db.py`      | Builds a local SQLite DB from the generated CSVs            |
| `data/csv/*.csv`                  | Generated CSV data (git-ignored, regenerate as needed)      |
| `data/insert_data.sql`            | Generated T-SQL INSERT statements (git-ignored)             |
| `data/playground.db`              | Generated local SQLite database (git-ignored)               |

See [`../README.md`](../README.md) for setup and usage instructions.
