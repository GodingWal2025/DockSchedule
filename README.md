# GXO Dock - Operations Hub (Azure Static Web App)

A Single Page Application (SPA) with a serverless Python API backend, optimized for deployment on Azure Static Web Apps. This application manages warehouse driver appointments and dock schedules (capturing appointments, check-in, check-out, dwell time, status, door assignment, and PIT operator tracking) and generates KPI exports suitable for Excel.

## Features

- **Today Dashboard** - Real-time statistics of appointments, checked-in drivers, completed, late, and missed counts.
- **Add Appointment** - Create IB/OB appointments with duplicate BOL warning and capacity checks.
- **Appointment List** - Search and filter by date, type, status, carrier, and customer.
- **Check-In** - BOL lookup, automatic status calculation (Early/On Time/Late), door, and PIT operator assignment.
- **Check-Out** - Automatic dwell time calculation and completion tracking.
- **KPI Export** - Tab-separated clipboard export + CSV download with exact Excel column mapping.
- **PIT App** - Integrated view for PIT board operators.

## Architecture

- **Frontend**: Single Page Application (SPA) located in the `frontend/` directory (HTML, Custom CSS, and Vanilla JavaScript).
- **Backend (API)**: Serverless Python API located in the `api/` directory (Azure Functions v2 programming model).
- **Database**: Local SQLite database (`db.sqlite3` in root directory) queried via parameterized sqlite3 connections.

---

## Local Development Quick Start

To run and test the Azure Static Web App locally:

### 1. Prerequisites
- **Node.js**: Needed to run the Azure Static Web Apps CLI.
- **Python 3.10+**: Needed for running the Azure Functions backend locally.
- **Azure Functions Core Tools**: The SWA CLI uses this under the hood to run the Python API. Install it via:
  ```bash
  npm install -g azure-functions-core-tools@4 --unsafe-perm true
  ```
- **Azure Static Web Apps CLI**: Install the SWA CLI globally:
  ```bash
  npm install -g @azure/static-web-apps-cli
  ```

### 2. Install Python Dependencies
Create a virtual environment and install the required API packages:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r api/requirements.txt
```

### 3. Start the SWA Development Server
Run the SWA CLI starting command:
```bash
swa start frontend --api-location api
```

This will spin up:
- The static frontend at `http://localhost:4280`
- The proxy which routes all `/api/*` requests to your local Azure Functions core tools running the `api/` backend.

---

## Business Rules

- **Early**: Check-in > 15 min before appointment time.
- **On Time**: Check-in within ±15 min of appointment time.
- **Late**: Check-in > 15 min after appointment time.
- **Dwell Time**: Check-Out Time - Check-In Time (auto-calculated in seconds, formatted as `HH:MM:SS`).
- **Duplicate BOL**: Warning shown on UI, allowing user override.
- **Capacity Rules**: Limits checked on appointment creation based on date, time, and direction.
