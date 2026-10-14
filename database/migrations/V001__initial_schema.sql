-- =============================================================================
-- Migration V001: Initial Multi-Tenant Schema Baseline
-- Description: Idempotent baseline schema definition for SalesManagementDB.
-- =============================================================================

-- 1. Companies (Tenants)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Companies')
BEGIN
    CREATE TABLE Companies (
        CompanyID INT IDENTITY(1,1) PRIMARY KEY,
        CompanyName NVARCHAR(150) NOT NULL UNIQUE,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- 2. Stores
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Stores')
BEGIN
    CREATE TABLE Stores (
        StoreID INT IDENTITY(1,1) PRIMARY KEY,
        CompanyID INT NOT NULL,
        StoreName NVARCHAR(150) NOT NULL,
        Location NVARCHAR(255) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Stores_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID),
        CONSTRAINT UQ_Stores_StoreID_CompanyID UNIQUE (StoreID, CompanyID),
        CONSTRAINT UQ_Store_Name_Per_Company UNIQUE (CompanyID, StoreName)
    );
END;
GO

-- 3. Roles & Permissions (RBAC)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Roles')
BEGIN
    CREATE TABLE Roles (
        RoleID INT PRIMARY KEY,
        RoleName NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Permissions')
BEGIN
    CREATE TABLE Permissions (
        PermissionID INT PRIMARY KEY,
        PermissionName NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RolePermissions')
BEGIN
    CREATE TABLE RolePermissions (
        RoleID INT NOT NULL,
        PermissionID INT NOT NULL,
        CONSTRAINT PK_RolePermissions PRIMARY KEY (RoleID, PermissionID),
        CONSTRAINT FK_RolePermissions_Role FOREIGN KEY (RoleID) REFERENCES Roles(RoleID),
        CONSTRAINT FK_RolePermissions_Permission FOREIGN KEY (PermissionID) REFERENCES Permissions(PermissionID)
    );
END;
GO

-- 4. Users
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
BEGIN
    CREATE TABLE Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(150) NOT NULL,
        Email NVARCHAR(255) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        IsSystemAdmin BIT NOT NULL DEFAULT 0,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- 5. UserCompanies (User-Tenant Memberships with Role & optional Store)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'UserCompanies')
BEGIN
    CREATE TABLE UserCompanies (
        UserCompanyID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        CompanyID INT NOT NULL,
        RoleID INT NOT NULL,
        StoreID INT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CONSTRAINT FK_UserCompanies_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
        CONSTRAINT FK_UserCompanies_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID),
        CONSTRAINT FK_UserCompanies_Role FOREIGN KEY (RoleID) REFERENCES Roles(RoleID),
        CONSTRAINT FK_UserCompanies_Store FOREIGN KEY (StoreID, CompanyID) REFERENCES Stores(StoreID, CompanyID),
        CONSTRAINT UQ_UserTenant UNIQUE (UserID, CompanyID)
    );
END;
GO

-- 6. Customers
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers')
BEGIN
    CREATE TABLE Customers (
        CustomerID VARCHAR(20) PRIMARY KEY,
        CustomerName NVARCHAR(150) NOT NULL,
        Segment VARCHAR(50) NULL,
        CompanyID INT NOT NULL,
        CONSTRAINT FK_Customers_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID)
    );
END;
GO

-- 7. Products
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Products')
BEGIN
    CREATE TABLE Products (
        ProductID VARCHAR(20) PRIMARY KEY,
        ProductName NVARCHAR(255) NOT NULL,
        Category VARCHAR(50) NULL,
        SubCategory VARCHAR(50) NULL,
        CompanyID INT NOT NULL,
        CONSTRAINT FK_Products_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID)
    );
END;
GO

-- 8. Orders
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Orders')
BEGIN
    CREATE TABLE Orders (
        OrderID VARCHAR(20) PRIMARY KEY,
        OrderDate DATE NOT NULL,
        ShipDate DATE NULL,
        ShipMode VARCHAR(50) NULL,
        CustomerID VARCHAR(20) NOT NULL,
        Country VARCHAR(50) NULL,
        City VARCHAR(50) NULL,
        State VARCHAR(50) NULL,
        PostalCode VARCHAR(20) NULL,
        Region VARCHAR(50) NULL,
        CompanyID INT NOT NULL,
        StoreID INT NULL,
        CONSTRAINT FK_Orders_Customer FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
        CONSTRAINT FK_Orders_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID),
        CONSTRAINT FK_Orders_Store FOREIGN KEY (StoreID, CompanyID) REFERENCES Stores(StoreID, CompanyID)
    );
END;
GO

-- 9. OrderDetails
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'OrderDetails')
BEGIN
    CREATE TABLE OrderDetails (
        OrderDetailID INT IDENTITY(1,1) PRIMARY KEY,
        OrderID VARCHAR(20) NOT NULL,
        ProductID VARCHAR(20) NOT NULL,
        Sales DECIMAL(10,2) NOT NULL,
        Quantity INT NOT NULL,
        Discount DECIMAL(5,2) NOT NULL,
        Profit DECIMAL(10,2) NOT NULL,
        CONSTRAINT FK_OrderDetails_Order FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
        CONSTRAINT FK_OrderDetails_Product FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
    );
END;
GO
