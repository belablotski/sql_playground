#!/usr/bin/env python3
"""
Build a local SQLite database from the generated CSV files, so you can
experiment with the playground schema without a SQL Server instance.

The table/column layout matches sql/schema.sql, adapted to SQLite syntax
(SQLite has no IDENTITY, BIT, or computed-column support in the same form
as T-SQL). Use sql/schema.sql as the source of truth for SQL Server.

Usage:
    python scripts/generate_data.py           # generates data/csv/*.csv
    python scripts/build_sqlite_db.py          # builds data/playground.db
"""
from __future__ import annotations

import csv
import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_DIR = os.path.join(DATA_DIR, "csv")
DB_PATH = os.path.join(DATA_DIR, "playground.db")

SCHEMA_SQLITE = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS OrderItems;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Customers;

CREATE TABLE Customers (
    CustomerID      INTEGER PRIMARY KEY,
    FirstName       TEXT NOT NULL,
    LastName        TEXT NOT NULL,
    Email           TEXT NOT NULL UNIQUE,
    Phone           TEXT,
    City            TEXT,
    Country         TEXT,
    RegisteredDate  TEXT NOT NULL
);

CREATE TABLE Employees (
    EmployeeID   INTEGER PRIMARY KEY,
    FirstName    TEXT NOT NULL,
    LastName     TEXT NOT NULL,
    Title        TEXT NOT NULL,
    HireDate     TEXT NOT NULL,
    ManagerID    INTEGER REFERENCES Employees (EmployeeID)
);

CREATE TABLE Categories (
    CategoryID    INTEGER PRIMARY KEY,
    CategoryName  TEXT NOT NULL UNIQUE,
    Description   TEXT
);

CREATE TABLE Products (
    ProductID       INTEGER PRIMARY KEY,
    ProductName     TEXT NOT NULL,
    CategoryID      INTEGER NOT NULL REFERENCES Categories (CategoryID),
    UnitPrice       REAL NOT NULL CHECK (UnitPrice >= 0),
    UnitsInStock    INTEGER NOT NULL DEFAULT 0 CHECK (UnitsInStock >= 0),
    Discontinued    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE Orders (
    OrderID      INTEGER PRIMARY KEY,
    CustomerID   INTEGER NOT NULL REFERENCES Customers (CustomerID),
    EmployeeID   INTEGER NOT NULL REFERENCES Employees (EmployeeID),
    OrderDate    TEXT NOT NULL,
    ShipDate     TEXT,
    Status       TEXT NOT NULL CHECK (Status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled'))
);

CREATE TABLE OrderItems (
    OrderItemID  INTEGER PRIMARY KEY,
    OrderID      INTEGER NOT NULL REFERENCES Orders (OrderID),
    ProductID    INTEGER NOT NULL REFERENCES Products (ProductID),
    Quantity     INTEGER NOT NULL CHECK (Quantity > 0),
    UnitPrice    REAL NOT NULL CHECK (UnitPrice >= 0),
    Discount     REAL NOT NULL DEFAULT 0 CHECK (Discount BETWEEN 0 AND 1),
    LineTotal    REAL GENERATED ALWAYS AS (Quantity * UnitPrice * (1 - Discount)) STORED
);

CREATE INDEX IX_Products_CategoryID ON Products (CategoryID);
CREATE INDEX IX_Orders_CustomerID ON Orders (CustomerID);
CREATE INDEX IX_Orders_EmployeeID ON Orders (EmployeeID);
CREATE INDEX IX_Orders_OrderDate ON Orders (OrderDate);
CREATE INDEX IX_OrderItems_OrderID ON OrderItems (OrderID);
CREATE INDEX IX_OrderItems_ProductID ON OrderItems (ProductID);
"""

TABLE_ORDER = ["Categories", "Customers", "Employees", "Products", "Orders", "OrderItems"]
BOOLEAN_COLUMNS = {"Discontinued"}


def load_csv(table: str) -> list[dict]:
    path = os.path.join(CSV_DIR, f"{table}.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def coerce(table: str, row: dict) -> dict:
    coerced = {}
    for key, value in row.items():
        if value == "":
            coerced[key] = None
        elif key in BOOLEAN_COLUMNS:
            coerced[key] = 1 if value in ("True", "1", "true") else 0
        else:
            coerced[key] = value
    return coerced


def main() -> None:
    if not os.path.isdir(CSV_DIR):
        raise SystemExit(
            f"CSV directory not found: {CSV_DIR}\n"
            "Run scripts/generate_data.py first."
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_SQLITE)

        for table in TABLE_ORDER:
            rows = load_csv(table)
            if not rows:
                continue
            rows = [coerce(table, r) for r in rows]
            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            col_list = ", ".join(columns)
            conn.executemany(
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
                [tuple(r[c] for c in columns) for r in rows],
            )
            print(f"Loaded {len(rows)} rows into {table}")

        conn.commit()
    finally:
        conn.close()

    print(f"SQLite database built at: {DB_PATH}")


if __name__ == "__main__":
    main()
