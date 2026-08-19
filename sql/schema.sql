-- ============================================================================
-- SQL Playground - Database Schema (Microsoft SQL Server / T-SQL dialect)
--
-- Domain: a small retail / e-commerce store.
-- See docs/DB_STRUCTURE.md for a full description of the tables and data.
--
-- Usage (SQL Server / Azure SQL / sqlcmd):
--   sqlcmd -S <server> -d <database> -i sql/schema.sql
-- ============================================================================

IF DB_ID('SqlPlayground') IS NULL
BEGIN
    PRINT 'Run this script against an existing database, or create one first:';
    PRINT '  CREATE DATABASE SqlPlayground;';
END
GO

-- Drop tables in dependency order (children first) so the script is re-runnable.
IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL DROP TABLE dbo.OrderItems;
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE dbo.Products;
IF OBJECT_ID('dbo.Categories', 'U') IS NOT NULL DROP TABLE dbo.Categories;
IF OBJECT_ID('dbo.Employees', 'U') IS NOT NULL DROP TABLE dbo.Employees;
IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL DROP TABLE dbo.Customers;
GO

-- ----------------------------------------------------------------------------
-- Customers
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.Customers
(
    CustomerID      INT IDENTITY(1,1) PRIMARY KEY,
    FirstName       NVARCHAR(50)  NOT NULL,
    LastName        NVARCHAR(50)  NOT NULL,
    Email           NVARCHAR(100) NOT NULL UNIQUE,
    Phone           NVARCHAR(25)  NULL,
    City            NVARCHAR(50)  NULL,
    Country         NVARCHAR(50)  NULL,
    RegisteredDate  DATE          NOT NULL DEFAULT (CAST(GETDATE() AS DATE))
);
GO

-- ----------------------------------------------------------------------------
-- Employees (self-referencing hierarchy: each employee may have a manager)
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.Employees
(
    EmployeeID   INT IDENTITY(1,1) PRIMARY KEY,
    FirstName    NVARCHAR(50) NOT NULL,
    LastName     NVARCHAR(50) NOT NULL,
    Title        NVARCHAR(50) NOT NULL,
    HireDate     DATE         NOT NULL,
    ManagerID    INT          NULL,
    CONSTRAINT FK_Employees_Manager FOREIGN KEY (ManagerID)
        REFERENCES dbo.Employees (EmployeeID)
);
GO

-- ----------------------------------------------------------------------------
-- Categories
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.Categories
(
    CategoryID    INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName  NVARCHAR(50)  NOT NULL UNIQUE,
    Description   NVARCHAR(255) NULL
);
GO

-- ----------------------------------------------------------------------------
-- Products
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.Products
(
    ProductID       INT IDENTITY(1,1) PRIMARY KEY,
    ProductName     NVARCHAR(100)  NOT NULL,
    CategoryID      INT            NOT NULL,
    UnitPrice       DECIMAL(10,2)  NOT NULL CHECK (UnitPrice >= 0),
    UnitsInStock    INT            NOT NULL DEFAULT 0 CHECK (UnitsInStock >= 0),
    Discontinued    BIT            NOT NULL DEFAULT 0,
    CONSTRAINT FK_Products_Categories FOREIGN KEY (CategoryID)
        REFERENCES dbo.Categories (CategoryID)
);
GO

-- ----------------------------------------------------------------------------
-- Orders
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.Orders
(
    OrderID      INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID   INT           NOT NULL,
    EmployeeID   INT           NOT NULL,
    OrderDate    DATETIME2     NOT NULL,
    ShipDate     DATETIME2     NULL,
    Status       NVARCHAR(20)  NOT NULL
        CHECK (Status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerID)
        REFERENCES dbo.Customers (CustomerID),
    CONSTRAINT FK_Orders_Employees FOREIGN KEY (EmployeeID)
        REFERENCES dbo.Employees (EmployeeID)
);
GO

-- ----------------------------------------------------------------------------
-- OrderItems (line items, many-to-many between Orders and Products)
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.OrderItems
(
    OrderItemID  INT IDENTITY(1,1) PRIMARY KEY,
    OrderID      INT            NOT NULL,
    ProductID    INT            NOT NULL,
    Quantity     INT            NOT NULL CHECK (Quantity > 0),
    UnitPrice    DECIMAL(10,2)  NOT NULL CHECK (UnitPrice >= 0),
    Discount     DECIMAL(4,3)   NOT NULL DEFAULT 0 CHECK (Discount BETWEEN 0 AND 1),
    LineTotal AS (CAST(Quantity * UnitPrice * (1 - Discount) AS DECIMAL(12,2))) PERSISTED,
    CONSTRAINT FK_OrderItems_Orders FOREIGN KEY (OrderID)
        REFERENCES dbo.Orders (OrderID),
    CONSTRAINT FK_OrderItems_Products FOREIGN KEY (ProductID)
        REFERENCES dbo.Products (ProductID)
);
GO

-- ----------------------------------------------------------------------------
-- Helpful indexes for common query patterns (joins / filters)
-- ----------------------------------------------------------------------------
CREATE INDEX IX_Products_CategoryID ON dbo.Products (CategoryID);
CREATE INDEX IX_Orders_CustomerID ON dbo.Orders (CustomerID);
CREATE INDEX IX_Orders_EmployeeID ON dbo.Orders (EmployeeID);
CREATE INDEX IX_Orders_OrderDate ON dbo.Orders (OrderDate);
CREATE INDEX IX_OrderItems_OrderID ON dbo.OrderItems (OrderID);
CREATE INDEX IX_OrderItems_ProductID ON dbo.OrderItems (ProductID);
GO
