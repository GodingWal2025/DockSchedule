-- ==============================================================================
-- DockSchedule PIT App Schema Update for Azure SQL (dbo schema)
-- ==============================================================================

-- 1. Create Staging Lane Table
CREATE TABLE dbo.pit_staginglane (
    id INT IDENTITY(1,1) PRIMARY KEY,
    lane_name NVARCHAR(20) NOT NULL,
    area NVARCHAR(100) NOT NULL DEFAULT '',
    active BIT NOT NULL DEFAULT 1
);

-- 2. Create PIT Task Table
CREATE TABLE dbo.pit_pittask (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_type NVARCHAR(20) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
    product_info NVARCHAR(500) NOT NULL DEFAULT '',
    notes NVARCHAR(MAX) NOT NULL DEFAULT '',
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    started_at DATETIME2 NULL,
    completed_at DATETIME2 NULL,
    duration_seconds INT NULL,
    auto_checkout_triggered BIT NOT NULL DEFAULT 0,
    appointment_id INT NULL FOREIGN KEY REFERENCES dbo.core_appointment(id) ON DELETE CASCADE,
    operator_id INT NULL FOREIGN KEY REFERENCES dbo.core_pitoperator(id),
    staging_lane_id INT NULL FOREIGN KEY REFERENCES dbo.pit_staginglane(id)
);

-- 3. Create Pick Task Table
CREATE TABLE dbo.pit_picktask (
    id INT IDENTITY(1,1) PRIMARY KEY,
    pick_number NVARCHAR(50) NOT NULL UNIQUE,
    quantity INT NOT NULL DEFAULT 1,
    priority NVARCHAR(10) NOT NULL DEFAULT 'Normal',
    from_location NVARCHAR(100) NOT NULL DEFAULT '',
    status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
    created_by NVARCHAR(100) NOT NULL DEFAULT '',
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    started_at DATETIME2 NULL,
    completed_at DATETIME2 NULL,
    duration_seconds INT NULL,
    notes NVARCHAR(MAX) NOT NULL DEFAULT '',
    customer_id INT NULL FOREIGN KEY REFERENCES dbo.core_customer(id),
    product_type_id INT NULL FOREIGN KEY REFERENCES dbo.core_producttype(id),
    operator_id INT NULL FOREIGN KEY REFERENCES dbo.core_pitoperator(id),
    staging_lane_id INT NULL FOREIGN KEY REFERENCES dbo.pit_staginglane(id)
);

-- Seed basic staging lanes
INSERT INTO dbo.pit_staginglane (lane_name, area, active)
VALUES 
('Lane 1', 'East', 1),
('Lane 2', 'East', 1),
('Lane 3', 'West', 1),
('Lane 4', 'West', 1);

