#!/usr/bin/env python3
"""
Generate synthetic test data for the SQL Playground database.

This script produces:
  1. CSV files (one per table) under ``data/csv`` for easy loading with
     ``BULK INSERT`` / ``bcp`` into SQL Server, or with any other tool.
  2. A single T-SQL script ``data/insert_data.sql`` containing ``INSERT``
     statements, ready to run against SQL Server with ``sqlcmd``.

The data is randomly generated (via Faker) but uses a fixed seed by default
so runs are reproducible.

Usage:
    python scripts/generate_data.py --customers 100 --employees 10 \
        --categories 8 --products 60 --orders 400 --seed 42
"""
from __future__ import annotations

import argparse
import csv
import os
import random
from datetime import timedelta

from faker import Faker

CATEGORY_NAMES = [
    "Electronics", "Books", "Home & Kitchen", "Toys", "Sports & Outdoors",
    "Clothing", "Beauty", "Groceries", "Automotive", "Office Supplies",
    "Garden", "Pet Supplies",
]

ORDER_STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled"]
EMPLOYEE_TITLES = ["Sales Representative", "Sales Manager", "Support Agent"]


def sql_str(value) -> str:
    """Format a Python value as a T-SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"N'{escaped}'"


def generate_categories(fake: Faker, count: int) -> list[dict]:
    names = CATEGORY_NAMES[:count] if count <= len(CATEGORY_NAMES) else (
        CATEGORY_NAMES + [f"Category {i}" for i in range(len(CATEGORY_NAMES), count)]
    )
    return [
        {
            "CategoryID": i + 1,
            "CategoryName": name,
            "Description": fake.sentence(nb_words=8),
        }
        for i, name in enumerate(names)
    ]


def generate_customers(fake: Faker, count: int) -> list[dict]:
    customers = []
    for i in range(count):
        registered = fake.date_between(start_date="-3y", end_date="today")
        customers.append(
            {
                "CustomerID": i + 1,
                "FirstName": fake.first_name(),
                "LastName": fake.last_name(),
                "Email": fake.unique.email(),
                "Phone": fake.phone_number()[:25],
                "City": fake.city(),
                "Country": fake.country(),
                "RegisteredDate": registered.isoformat(),
            }
        )
    return customers


def generate_employees(fake: Faker, count: int) -> list[dict]:
    employees = []
    for i in range(count):
        manager_id = None
        # First employee has no manager; others report to an earlier employee.
        if i > 0:
            manager_id = random.randint(1, i)
        employees.append(
            {
                "EmployeeID": i + 1,
                "FirstName": fake.first_name(),
                "LastName": fake.last_name(),
                "Title": random.choice(EMPLOYEE_TITLES) if i > 0 else "Sales Manager",
                "HireDate": fake.date_between(start_date="-5y", end_date="-1y").isoformat(),
                "ManagerID": manager_id,
            }
        )
    return employees


def generate_products(fake: Faker, count: int, categories: list[dict]) -> list[dict]:
    products = []
    for i in range(count):
        products.append(
            {
                "ProductID": i + 1,
                "ProductName": fake.unique.catch_phrase(),
                "CategoryID": random.choice(categories)["CategoryID"],
                "UnitPrice": round(random.uniform(2.5, 500.0), 2),
                "UnitsInStock": random.randint(0, 500),
                "Discontinued": random.random() < 0.05,
            }
        )
    return products


def generate_orders_and_items(
    fake: Faker,
    order_count: int,
    customers: list[dict],
    employees: list[dict],
    products: list[dict],
) -> tuple[list[dict], list[dict]]:
    orders = []
    order_items = []
    item_id = 1
    for i in range(order_count):
        order_id = i + 1
        order_date = fake.date_time_between(start_date="-2y", end_date="now")
        status = random.choices(
            ORDER_STATUSES, weights=[0.15, 0.25, 0.55, 0.05], k=1
        )[0]
        ship_date = None
        if status in ("Shipped", "Delivered"):
            ship_date = order_date + timedelta(days=random.randint(1, 10))

        orders.append(
            {
                "OrderID": order_id,
                "CustomerID": random.choice(customers)["CustomerID"],
                "EmployeeID": random.choice(employees)["EmployeeID"],
                "OrderDate": order_date.isoformat(sep=" "),
                "ShipDate": ship_date.isoformat(sep=" ") if ship_date else None,
                "Status": status,
            }
        )

        line_item_count = random.randint(1, min(5, len(products)))
        for product in random.sample(products, k=line_item_count):
            order_items.append(
                {
                    "OrderItemID": item_id,
                    "OrderID": order_id,
                    "ProductID": product["ProductID"],
                    "Quantity": random.randint(1, 10),
                    "UnitPrice": product["UnitPrice"],
                    "Discount": random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2]),
                }
            )
            item_id += 1

    return orders, order_items


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_sql_inserts(path: str, table_rows: list[tuple[str, list[dict]]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("-- Auto-generated by scripts/generate_data.py. Do not edit by hand.\n")
        f.write("-- Run with: sqlcmd -S <server> -d <database> -i data/insert_data.sql\n\n")
        for table, rows in table_rows:
            if not rows:
                continue
            f.write(f"-- {table} ({len(rows)} rows)\n")
            f.write(f"SET IDENTITY_INSERT dbo.{table} ON;\n")
            columns = list(rows[0].keys())
            col_list = ", ".join(columns)
            for row in rows:
                values = ", ".join(sql_str(row[c]) for c in columns)
                f.write(f"INSERT INTO dbo.{table} ({col_list}) VALUES ({values});\n")
            f.write(f"SET IDENTITY_INSERT dbo.{table} OFF;\nGO\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--categories", type=int, default=10)
    parser.add_argument("--customers", type=int, default=100)
    parser.add_argument("--employees", type=int, default=8)
    parser.add_argument("--products", type=int, default=60)
    parser.add_argument("--orders", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data"),
        help="Directory to write generated data into (default: ../data)",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    categories = generate_categories(fake, args.categories)
    customers = generate_customers(fake, args.customers)
    employees = generate_employees(fake, args.employees)
    products = generate_products(fake, args.products, categories)
    orders, order_items = generate_orders_and_items(
        fake, args.orders, customers, employees, products
    )

    output_dir = os.path.abspath(args.output_dir)
    csv_dir = os.path.join(output_dir, "csv")

    write_csv(os.path.join(csv_dir, "Categories.csv"), categories)
    write_csv(os.path.join(csv_dir, "Customers.csv"), customers)
    write_csv(os.path.join(csv_dir, "Employees.csv"), employees)
    write_csv(os.path.join(csv_dir, "Products.csv"), products)
    write_csv(os.path.join(csv_dir, "Orders.csv"), orders)
    write_csv(os.path.join(csv_dir, "OrderItems.csv"), order_items)

    write_sql_inserts(
        os.path.join(output_dir, "insert_data.sql"),
        [
            ("Categories", categories),
            ("Customers", customers),
            ("Employees", employees),
            ("Products", products),
            ("Orders", orders),
            ("OrderItems", order_items),
        ],
    )

    print(f"Generated {len(categories)} categories, {len(customers)} customers, "
          f"{len(employees)} employees, {len(products)} products, "
          f"{len(orders)} orders, {len(order_items)} order items.")
    print(f"CSV files written to: {csv_dir}")
    print(f"SQL insert script written to: {os.path.join(output_dir, 'insert_data.sql')}")


if __name__ == "__main__":
    main()
