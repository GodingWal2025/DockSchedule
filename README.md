# AMB Driver Log Website

A locally hosted Django web application for warehouse driver appointment and dock management. Captures daily operational data (appointments, check-in, check-out, dwell time, status, door assignment, PIT operator tracking) and exports a copy/paste table for Excel KPI workbook integration.

## Features

- **Today Dashboard** - Real-time overview of appointments, checked-in drivers, completed, late, missed counts
- **Add Appointment** - Create IB/OB appointments with duplicate BOL warning and capacity check
- **Appointment List** - Search and filter by date, type, status, carrier, customer
- **Check-In** - BOL lookup, automatic status calculation (Early/On Time/Late), door/PIT assignment
- **Check-Out** - Automatic dwell time calculation, completion tracking
- **KPI Export** - Tab-separated clipboard export + CSV download with exact Excel column mapping

## Tech Stack

- **Backend**: Django 5.x + Python 3.12
- **Database**: SQLite (MVP, upgrade to PostgreSQL for production)
- **Frontend**: Django Templates + Bootstrap 5.3 + Bootstrap Icons
- **Export**: Tab-separated (clipboard) + CSV (download)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Seed Reference Data

```bash
python manage.py seed_data
```

This creates sample customers, carriers, product types, doors, PIT operators, and capacity rules.

### 4. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access at `http://localhost:8000`

Admin panel at `http://localhost:8000/admin`

## Deployment (Local Server)

For local network deployment on a mini PC or server:

### Using Django Development Server (for testing)

```bash
python manage.py runserver 0.0.0.0:8000
```

### Using Gunicorn (recommended for production)

```bash
pip install gunicorn
gunicorn amb_driver_log.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Systemd Service (Linux)

Create `/etc/systemd/system/amb-driver-log.service`:

```ini
[Unit]
Description=AMB Driver Log Website
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/amb_driver_log
ExecStart=/path/to/venv/bin/gunicorn amb_driver_log.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable amb-driver-log
sudo systemctl start amb-driver-log
```

### Network Access

Set your server's IP or hostname in `ALLOWED_HOSTS` in `amb_driver_log/settings.py`:

```python
ALLOWED_HOSTS = ['192.168.1.100', 'amb-driver-log.local', 'localhost', '127.0.0.1']
```

Users access via `http://192.168.1.100:8000` or `http://amb-driver-log.local:8000`

## Daily Operating Process

### During the Day
1. Add appointments in the website
2. Check drivers in using BOL lookup
3. Assign door and PIT operator
4. Check drivers out
5. Website calculates status and dwell time automatically

### End of Day / Next Morning
1. Open KPI Export screen
2. Select yesterday's date range
3. Click Preview Export
4. Click Copy to Clipboard
5. Open Excel KPI workbook
6. Paste into WEB_IMPORT sheet
7. Refresh KPIs/graphs
8. Save workbook

## Export Column Format

The KPI Export outputs these columns in exact order for Excel:

1. Appt_Type (IB/OB)
2. In (check-in datetime: M/D/YYYY H:MM AM/PM)
3. Out (check-out datetime: M/D/YYYY H:MM AM/PM)
4. Appt_Time (scheduled datetime: M/D/YYYY H:MM AM/PM)
5. Status (Scheduled/Checked In/Completed/Early/On Time/Late/Missed/Cancelled)
6. Customer
7. Type (product type)
8. Carrier
9. BOL-Shipment_No
10. Visitor_Name
11. Delivery_No
12. Trailer_No
13. Drivers_License_State
14. Load_Lock (Y/N/NA)
15. Assigned_Door
16. Dwell_Time (HH:MM:SS)
17. Notes
18. PIT_Operator
19. InOutStatus (In/Out)
20. Color_Coding (reserved)
21. Appt_Day (weekday name)
22. Appt_Slot (Excel time fraction, e.g. 0.3333 for 8:00 AM)
23. Appt_Month
24. Appt_Year

## Backup and Recovery

### Database Backup Script

Add a cron job for daily backups:

```bash
# /etc/cron.d/amb-backup
59 23 * * * your-user cp /path/to/db.sqlite3 /backup/amb_driver_log_$(date +\%Y\%m\%d).db
```

Keep the last 30 daily backups and 8 weekly backups.

## Project Structure

```
amb_driver_log/
├── amb_driver_log/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                     # Main application
│   ├── models.py             # All database models
│   ├── views.py              # All view functions
│   ├── forms.py              # All forms
│   ├── admin.py              # Admin configuration
│   ├── urls.py               # URL routing
│   ├── utils.py              # Export utilities
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── appointment_add.html
│   │   ├── appointment_list.html
│   │   ├── appointment_detail.html
│   │   ├── check_in.html
│   │   ├── check_out.html
│   │   └── kpi_export.html
│   ├── static/css/           # Custom styles
│   ├── fixtures/             # Seed data
│   └── management/commands/  # Custom management commands
├── db.sqlite3                # SQLite database
├── manage.py                 # Django management
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/appointments/` | JSON list of appointments (with filters) |
| `/api/check-bol/?bol=XXX` | Check for duplicate BOL numbers |
| `/api/capacity-check/?date=YYYY-MM-DD&time=HH:MM&appt_type=IB` | Check slot capacity |
| `/api/appointment-stats/?date=YYYY-MM-DD` | Dashboard statistics |

## Business Rules

- **Early**: Check-in > 15 min before appointment time
- **On Time**: Check-in within ±15 min of appointment time
- **Late**: Check-in > 15 min after appointment time
- **Dwell Time**: Check-Out Time - Check-In Time (auto-calculated)
- **Duplicate BOL**: Warning shown, user can continue with override
- **Capacity**: Warning when slot is at/beyond configured limit

## License

Internal use for AMB warehouse operations.
