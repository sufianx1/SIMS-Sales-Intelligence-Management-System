-- =============================================================================
-- Migration V004: Seed Roles and Permissions
-- Description: Ensures standard RBAC roles and permissions exist and are mapped.
-- =============================================================================

-- 1. Ensure Read-Only Analyst role exists
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'Read-Only Analyst')
BEGIN
    INSERT INTO Roles (RoleName) VALUES ('Read-Only Analyst');
END;
GO

-- 2. Ensure Permissions exist (without hardcoding Identity IDs)
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'VIEW_PRODUCTS')
    INSERT INTO Permissions (PermissionName) VALUES ('VIEW_PRODUCTS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'CREATE_PRODUCT')
    INSERT INTO Permissions (PermissionName) VALUES ('CREATE_PRODUCT');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'UPDATE_PRODUCT')
    INSERT INTO Permissions (PermissionName) VALUES ('UPDATE_PRODUCT');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'DELETE_PRODUCT')
    INSERT INTO Permissions (PermissionName) VALUES ('DELETE_PRODUCT');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'VIEW_CUSTOMERS')
    INSERT INTO Permissions (PermissionName) VALUES ('VIEW_CUSTOMERS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'CREATE_CUSTOMER')
    INSERT INTO Permissions (PermissionName) VALUES ('CREATE_CUSTOMER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'UPDATE_CUSTOMER')
    INSERT INTO Permissions (PermissionName) VALUES ('UPDATE_CUSTOMER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'DELETE_CUSTOMER')
    INSERT INTO Permissions (PermissionName) VALUES ('DELETE_CUSTOMER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'VIEW_ORDERS')
    INSERT INTO Permissions (PermissionName) VALUES ('VIEW_ORDERS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'CREATE_ORDER')
    INSERT INTO Permissions (PermissionName) VALUES ('CREATE_ORDER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'UPDATE_ORDER')
    INSERT INTO Permissions (PermissionName) VALUES ('UPDATE_ORDER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'DELETE_ORDER')
    INSERT INTO Permissions (PermissionName) VALUES ('DELETE_ORDER');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'VIEW_REPORTS')
    INSERT INTO Permissions (PermissionName) VALUES ('VIEW_REPORTS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'MANAGE_USERS')
    INSERT INTO Permissions (PermissionName) VALUES ('MANAGE_USERS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'MANAGE_TENANTS')
    INSERT INTO Permissions (PermissionName) VALUES ('MANAGE_TENANTS');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'MANAGE_ROLES')
    INSERT INTO Permissions (PermissionName) VALUES ('MANAGE_ROLES');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'MANAGE_COMPANIES')
    INSERT INTO Permissions (PermissionName) VALUES ('MANAGE_COMPANIES');
IF NOT EXISTS (SELECT 1 FROM Permissions WHERE PermissionName = 'MANAGE_STORES')
    INSERT INTO Permissions (PermissionName) VALUES ('MANAGE_STORES');
GO

-- 3. Map Role Permissions for Read-Only Analyst
INSERT INTO RolePermissions (RoleID, PermissionID)
SELECT r.RoleID, p.PermissionID
FROM Roles r
CROSS JOIN Permissions p
WHERE r.RoleName = 'Read-Only Analyst'
  AND p.PermissionName IN ('VIEW_REPORTS', 'VIEW_PRODUCTS', 'VIEW_CUSTOMERS', 'VIEW_ORDERS')
  AND NOT EXISTS (
      SELECT 1 FROM RolePermissions rp WHERE rp.RoleID = r.RoleID AND rp.PermissionID = p.PermissionID
  );
GO
