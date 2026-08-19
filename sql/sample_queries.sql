-- ============================================================================
-- Sample T-SQL queries to experiment with the playground schema.
-- Works against SQL Server. For SQLite, replace TOP n with LIMIT n,
-- GETDATE() with datetime('now'), and DATEDIFF/DATEADD with SQLite equivalents.
-- ============================================================================

-- 1. Top 10 customers by total spend
SELECT TOP 10
    c.CustomerID,
    c.FirstName + ' ' + c.LastName AS CustomerName,
    SUM(oi.LineTotal) AS TotalSpend
FROM dbo.Customers c
JOIN dbo.Orders o ON o.CustomerID = c.CustomerID
JOIN dbo.OrderItems oi ON oi.OrderID = o.OrderID
GROUP BY c.CustomerID, c.FirstName, c.LastName
ORDER BY TotalSpend DESC;

-- 2. Monthly revenue trend
SELECT
    DATEFROMPARTS(YEAR(o.OrderDate), MONTH(o.OrderDate), 1) AS OrderMonth,
    SUM(oi.LineTotal) AS Revenue,
    COUNT(DISTINCT o.OrderID) AS OrderCount
FROM dbo.Orders o
JOIN dbo.OrderItems oi ON oi.OrderID = o.OrderID
GROUP BY DATEFROMPARTS(YEAR(o.OrderDate), MONTH(o.OrderDate), 1)
ORDER BY OrderMonth;

-- 3. Best-selling products by category
SELECT
    cat.CategoryName,
    p.ProductName,
    SUM(oi.Quantity) AS UnitsSold,
    SUM(oi.LineTotal) AS Revenue
FROM dbo.Products p
JOIN dbo.Categories cat ON cat.CategoryID = p.CategoryID
JOIN dbo.OrderItems oi ON oi.ProductID = p.ProductID
GROUP BY cat.CategoryName, p.ProductName
ORDER BY cat.CategoryName, Revenue DESC;

-- 4. Employees and their managers (self-join)
SELECT
    e.EmployeeID,
    e.FirstName + ' ' + e.LastName AS Employee,
    m.FirstName + ' ' + m.LastName AS Manager
FROM dbo.Employees e
LEFT JOIN dbo.Employees m ON m.EmployeeID = e.ManagerID
ORDER BY e.EmployeeID;

-- 5. Window function: rank customers within their country by spend
SELECT
    c.Country,
    c.CustomerID,
    c.FirstName + ' ' + c.LastName AS CustomerName,
    SUM(oi.LineTotal) AS TotalSpend,
    RANK() OVER (PARTITION BY c.Country ORDER BY SUM(oi.LineTotal) DESC) AS RankInCountry
FROM dbo.Customers c
JOIN dbo.Orders o ON o.CustomerID = c.CustomerID
JOIN dbo.OrderItems oi ON oi.OrderID = o.OrderID
GROUP BY c.Country, c.CustomerID, c.FirstName, c.LastName;

-- 6. Orders that took longer than 5 days to ship
SELECT
    o.OrderID,
    o.OrderDate,
    o.ShipDate,
    DATEDIFF(day, o.OrderDate, o.ShipDate) AS DaysToShip
FROM dbo.Orders o
WHERE o.ShipDate IS NOT NULL
  AND DATEDIFF(day, o.OrderDate, o.ShipDate) > 5
ORDER BY DaysToShip DESC;

-- 7. Products that are low on stock and not discontinued
SELECT ProductID, ProductName, UnitsInStock
FROM dbo.Products
WHERE UnitsInStock < 10 AND Discontinued = 0
ORDER BY UnitsInStock;

-- 8. Common Table Expression: customer lifetime value quartiles
WITH CustomerSpend AS (
    SELECT
        c.CustomerID,
        SUM(oi.LineTotal) AS TotalSpend
    FROM dbo.Customers c
    JOIN dbo.Orders o ON o.CustomerID = c.CustomerID
    JOIN dbo.OrderItems oi ON oi.OrderID = o.OrderID
    GROUP BY c.CustomerID
)
SELECT
    CustomerID,
    TotalSpend,
    NTILE(4) OVER (ORDER BY TotalSpend DESC) AS SpendQuartile
FROM CustomerSpend;
