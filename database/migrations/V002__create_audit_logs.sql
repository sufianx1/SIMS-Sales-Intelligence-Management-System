-- =============================================================================
-- Migration V002: Create AuditLogs Table
-- Description: Creates the AuditLogs entity and indexing for multi-tenant auditability.
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AuditLogs')
BEGIN
    CREATE TABLE AuditLogs (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NULL,
        CompanyID INT NULL,
        Action VARCHAR(50) NOT NULL,
        EntityName VARCHAR(50) NULL,
        EntityID VARCHAR(50) NULL,
        Details NVARCHAR(MAX) NULL,
        IPAddress VARCHAR(45) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_AuditLogs_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
        CONSTRAINT FK_AuditLogs_Company FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID)
    );

    CREATE NONCLUSTERED INDEX IX_AuditLogs_CompanyID_CreatedAt 
        ON AuditLogs (CompanyID, CreatedAt DESC);

    CREATE NONCLUSTERED INDEX IX_AuditLogs_UserID_CreatedAt 
        ON AuditLogs (UserID, CreatedAt DESC);
END;
GO
