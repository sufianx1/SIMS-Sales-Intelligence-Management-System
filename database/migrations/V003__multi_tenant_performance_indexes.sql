-- =============================================================================
-- Migration V003: Multi-Tenant Performance Indexes
-- Description: Idempotently creates covering indexes for high-speed tenant slicing.
-- =============================================================================

-- 1. Orders by Company and Order Date
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Orders_CompanyID_OrderDate' AND object_id = OBJECT_ID('Orders'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_Orders_CompanyID_OrderDate 
        ON Orders (CompanyID, OrderDate DESC)
        INCLUDE (CustomerID, StoreID, Region, ShipMode);
END;
GO

-- 2. Customers by Company and Name
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Customers_CompanyID_Name' AND object_id = OBJECT_ID('Customers'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_Customers_CompanyID_Name 
        ON Customers (CompanyID, CustomerName)
        INCLUDE (Segment);
END;
GO

-- 3. Products by Company and Category
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Products_CompanyID_Category' AND object_id = OBJECT_ID('Products'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_Products_CompanyID_Category 
        ON Products (CompanyID, Category, SubCategory)
        INCLUDE (ProductName);
END;
GO

-- 4. OrderDetails by OrderID
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_OrderDetails_OrderID' AND object_id = OBJECT_ID('OrderDetails'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_OrderDetails_OrderID 
        ON OrderDetails (OrderID)
        INCLUDE (ProductID, Sales, Quantity, Discount, Profit);
END;
GO

-- 5. OrderDetails by ProductID
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_OrderDetails_ProductID' AND object_id = OBJECT_ID('OrderDetails'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_OrderDetails_ProductID 
        ON OrderDetails (ProductID)
        INCLUDE (Sales, Quantity, Profit);
END;
GO
