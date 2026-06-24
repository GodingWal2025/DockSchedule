-- ==========================================
-- GXO DockSchedule Azure SQL Database DDL
-- Execute this script in your Azure SQL Database to initialize the schema.
-- ==========================================

-- 1. Create Lookup Tables
CREATE TABLE dbo.core_customer (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE dbo.core_carrier (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE dbo.core_producttype (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE dbo.core_pitoperator (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    initials NVARCHAR(10) NOT NULL,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE dbo.core_door (
    id INT IDENTITY(1,1) PRIMARY KEY,
    door_name NVARCHAR(50) NOT NULL,
    area NVARCHAR(100) NOT NULL DEFAULT 'Main Dock',
    direction NVARCHAR(10) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'Open',
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE dbo.core_capacityrule (
    id INT IDENTITY(1,1) PRIMARY KEY,
    month INT NOT NULL,
    day_of_week INT NOT NULL,
    time_slot TIME NOT NULL,
    appt_type NVARCHAR(10) NOT NULL,
    max_appointments INT NOT NULL DEFAULT 5,
    active BIT NOT NULL DEFAULT 1
);

-- 2. Create Appointment Table
CREATE TABLE dbo.core_appointment (
    id INT IDENTITY(1,1) PRIMARY KEY,
    appt_type NVARCHAR(2) NOT NULL,
    appt_date DATE NOT NULL,
    appt_time TIME NOT NULL,
    scheduled_datetime DATETIME2 NOT NULL,
    bol_shipment_no NVARCHAR(100) NOT NULL,
    delivery_no NVARCHAR(100) NOT NULL DEFAULT '',
    status NVARCHAR(20) NOT NULL DEFAULT 'Scheduled',
    notes NVARCHAR(MAX) NOT NULL DEFAULT '',
    created_at DATETIME2 NOT NULL,
    created_by NVARCHAR(100) NOT NULL DEFAULT '',
    updated_at DATETIME2 NOT NULL,
    cancelled_at DATETIME2 NULL,
    cancelled_reason NVARCHAR(MAX) NOT NULL DEFAULT '',
    carrier_id INT NOT NULL FOREIGN KEY REFERENCES dbo.core_carrier(id),
    customer_id INT NOT NULL FOREIGN KEY REFERENCES dbo.core_customer(id),
    product_type_id INT NOT NULL FOREIGN KEY REFERENCES dbo.core_producttype(id)
);

-- 3. Create Driver Visit Table
CREATE TABLE dbo.core_drivervisit (
    id INT IDENTITY(1,1) PRIMARY KEY,
    visitor_name NVARCHAR(200) NOT NULL,
    trailer_no NVARCHAR(100) NOT NULL,
    drivers_license_state NVARCHAR(50) NOT NULL,
    load_lock NVARCHAR(2) NOT NULL,
    check_in_time DATETIME2 NULL,
    check_out_time DATETIME2 NULL,
    dwell_seconds INT NULL,
    in_out_status NVARCHAR(3) NOT NULL,
    notes NVARCHAR(MAX) NOT NULL DEFAULT '',
    appointment_id INT NOT NULL UNIQUE FOREIGN KEY REFERENCES dbo.core_appointment(id),
    assigned_door_id INT NULL FOREIGN KEY REFERENCES dbo.core_door(id),
    pit_operator_id INT NULL FOREIGN KEY REFERENCES dbo.core_pitoperator(id)
);

-- 4. Create Audit Log Table
CREATE TABLE dbo.core_auditlog (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id NVARCHAR(100) NOT NULL,
    action NVARCHAR(20) NOT NULL,
    record_type NVARCHAR(50) NOT NULL,
    record_id INT NOT NULL,
    old_value NVARCHAR(MAX) NOT NULL,
    new_value NVARCHAR(MAX) NOT NULL,
    timestamp DATETIME2 NOT NULL
);

-- ==========================================
-- Insert Seed / Initial Data
-- ==========================================
INSERT INTO dbo.core_customer (name, active) VALUES 
('Bayer', 1), ('Monsanto', 1), ('Pioneer', 1);

INSERT INTO dbo.core_carrier (name, active) VALUES 
('Swift', 1), ('Schneider', 1), ('J.B. Hunt', 1), ('Werner', 1);

INSERT INTO dbo.core_producttype (name, active) VALUES 
('Corn', 1), ('Soybeans', 1), ('Wheat', 1);

INSERT INTO dbo.core_pitoperator (name, initials, active) VALUES 
('John Doe', 'JD', 1), ('Jane Smith', 'JS', 1);

INSERT INTO dbo.core_door (door_name, area, direction, status, active) VALUES 
('Door 1', 'East Dock', 'IB', 'Open', 1),
('Door 2', 'East Dock', 'IB', 'Open', 1),
('Door 3', 'West Dock', 'OB', 'Open', 1),
('Door 4', 'West Dock', 'OB', 'Open', 1);
