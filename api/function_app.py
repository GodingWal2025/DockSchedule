import os
import json
import sqlite3
import datetime
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Database connection helper
def get_db_connection():
    db_path = os.environ.get("DB_PATH", "../db.sqlite3")
    if not os.path.isabs(db_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.normpath(os.path.join(current_dir, db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Helper: JSON response wrapper
def json_response(data, status_code=200):
    return func.HttpResponse(
        body=json.dumps(data),
        mimetype="application/json",
        status_code=status_code
    )

# ─── 1. Metadata Lookup Endpoint ─────────────────────────────────────────────
@app.route(route="meta-data", methods=["GET"])
def get_metadata(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = get_db_connection()
        
        customers = [dict(r) for r in conn.execute("SELECT id, name FROM core_customer WHERE active = 1 ORDER BY name")]
        carriers = [dict(r) for r in conn.execute("SELECT id, name FROM core_carrier WHERE active = 1 ORDER BY name")]
        product_types = [dict(r) for r in conn.execute("SELECT id, name FROM core_producttype WHERE active = 1 ORDER BY name")]
        doors = [dict(r) for r in conn.execute("SELECT id, door_name, direction, status FROM core_door WHERE active = 1 ORDER BY door_name")]
        operators = [dict(r) for r in conn.execute("SELECT id, name, initials FROM core_pitoperator WHERE active = 1 ORDER BY name")]
        
        conn.close()
        
        return json_response({
            "customers": customers,
            "carriers": carriers,
            "productTypes": product_types,
            "doors": doors,
            "operators": operators
        })
    except Exception as e:
        return json_response({"error": str(e)}, status_code=500)

# ─── 2. Appointment Stats Endpoint ───────────────────────────────────────────
@app.route(route="appointment-stats", methods=["GET"])
def get_appointment_stats(req: func.HttpRequest) -> func.HttpResponse:
    try:
        date_str = req.params.get("date")
        if not date_str:
            date_str = datetime.date.today().isoformat()
            
        conn = get_db_connection()
        
        total = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND status != 'Cancelled'", (date_str,)).fetchone()[0]
        checked_in = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND status = 'Checked In'", (date_str,)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND status = 'Completed'", (date_str,)).fetchone()[0]
        late = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND status = 'Late'", (date_str,)).fetchone()[0]
        missed = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND status = 'Missed'", (date_str,)).fetchone()[0]
        
        ib_count = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND appt_type = 'IB' AND status != 'Cancelled'", (date_str,)).fetchone()[0]
        ob_count = conn.execute("SELECT COUNT(*) FROM core_appointment WHERE appt_date = ? AND appt_type = 'OB' AND status != 'Cancelled'", (date_str,)).fetchone()[0]
        
        conn.close()
        
        return json_response({
            "total": total,
            "checked_in": checked_in,
            "completed": completed,
            "late": late,
            "missed": missed,
            "ib_count": ib_count,
            "ob_count": ob_count
        })
    except Exception as e:
        return json_response({"error": str(e)}, status_code=500)

# ─── 3. Appointments List / Search Endpoint ──────────────────────────────────
@app.route(route="appointments", methods=["GET", "POST"])
def appointments(req: func.HttpRequest) -> func.HttpResponse:
    conn = get_db_connection()
    
    # POST - Create Appointment
    if req.method == 'POST':
        try:
            body = req.get_json()
            appt_type = body.get("appt_type")
            appt_date = body.get("appt_date")
            appt_time = body.get("appt_time")
            customer_id = body.get("customer_id")
            carrier_id = body.get("carrier_id")
            product_type_id = body.get("product_type_id")
            bol_shipment_no = body.get("bol_shipment_no", "")
            delivery_no = body.get("delivery_no", "")
            notes = body.get("notes", "")
            
            if not all([appt_type, appt_date, appt_time, customer_id, carrier_id, product_type_id]):
                return json_response({"error": "Missing required fields"}, status_code=400)
            
            # Combine date and time
            scheduled_datetime = f"{appt_date} {appt_time}:00"
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            updated_at = created_at
            
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO core_appointment 
                   (appt_type, appt_date, appt_time, scheduled_datetime, bol_shipment_no, delivery_no, status, notes, created_at, updated_at, carrier_id, customer_id, product_type_id, created_by, cancelled_reason)
                   VALUES (?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?, ?, ?, ?, '', '')""",
                (appt_type, appt_date, appt_time, scheduled_datetime, bol_shipment_no, delivery_no, notes, created_at, updated_at, carrier_id, customer_id, product_type_id)
            )
            
            # Insert empty audit log
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            return json_response({"success": True, "id": new_id})
        except Exception as e:
            conn.close()
            return json_response({"error": str(e)}, status_code=500)

    # GET - List Appointments
    try:
        q = req.params.get("q", "").strip()
        status_filter = req.params.get("status", "").strip()
        appt_type = req.params.get("appt_type", "").strip()
        date_from = req.params.get("date_from", "").strip()
        date_to = req.params.get("date_to", "").strip()
        
        sql = """
            SELECT a.*, 
                   cust.name as customer, 
                   carr.name as carrier, 
                   pt.name as product_type,
                   v.visitor_name, v.trailer_no, v.check_in_time, v.check_out_time, v.dwell_seconds, d.door_name, op.name as pit_operator
            FROM core_appointment a
            LEFT JOIN core_customer cust ON a.customer_id = cust.id
            LEFT JOIN core_carrier carr ON a.carrier_id = carr.id
            LEFT JOIN core_producttype pt ON a.product_type_id = pt.id
            LEFT JOIN core_drivervisit v ON a.id = v.appointment_id
            LEFT JOIN core_door d ON v.assigned_door_id = d.id
            LEFT JOIN core_pitoperator op ON v.pit_operator_id = op.id
            WHERE 1=1
        """
        params = []
        
        if q:
            sql += """ AND (a.bol_shipment_no LIKE ? OR cust.name LIKE ? OR carr.name LIKE ? 
                       OR v.visitor_name LIKE ? OR v.trailer_no LIKE ?)"""
            like_val = f"%{q}%"
            params.extend([like_val, like_val, like_val, like_val, like_val])
            
        if status_filter:
            sql += " AND a.status = ?"
            params.append(status_filter)
            
        if appt_type:
            sql += " AND a.appt_type = ?"
            params.append(appt_type)
            
        if date_from:
            sql += " AND a.appt_date >= ?"
            params.append(date_from)
            
        if date_to:
            sql += " AND a.appt_date <= ?"
            params.append(date_to)
            
        sql += " ORDER BY a.scheduled_datetime DESC LIMIT 100"
        
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        
        appointments = [dict(r) for r in rows]
        return json_response({"appointments": appointments})
    except Exception as e:
        conn.close()
        return json_response({"error": str(e)}, status_code=500)

# ─── 4. Check BOL Number Endpoint ────────────────────────────────────────────
@app.route(route="check-bol", methods=["GET"])
def check_bol(req: func.HttpRequest) -> func.HttpResponse:
    try:
        bol = req.params.get("bol", "").strip()
        if not bol:
            return json_response({"exists": False})
            
        conn = get_db_connection()
        row = conn.execute(
            "SELECT id FROM core_appointment WHERE bol_shipment_no = ? AND status != 'Cancelled' LIMIT 1",
            (bol,)
        ).fetchone()
        conn.close()
        
        return json_response({"exists": row is not None})
    except Exception as e:
        return json_response({"error": str(e)}, status_code=500)

# ─── 5. Slot Capacity Check Endpoint ─────────────────────────────────────────
@app.route(route="capacity-check", methods=["GET"])
def capacity_check(req: func.HttpRequest) -> func.HttpResponse:
    try:
        date_str = req.params.get("date")
        time_str = req.params.get("time")
        appt_type = req.params.get("appt_type")
        
        if not all([date_str, time_str, appt_type]):
            return json_response({"error": "Missing parameters"}, status_code=400)
            
        conn = get_db_connection()
        
        # Get day of week (Monday=0, Sunday=6)
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        day_of_week = date_obj.weekday()
        month = date_obj.month
        
        # Find capacity rule
        rule_row = conn.execute(
            """SELECT max_appointments FROM core_capacityrule 
               WHERE day_of_week = ? AND time_slot LIKE ? AND appt_type IN (?, 'Both') AND active = 1 LIMIT 1""",
            (day_of_week, f"{time_str}%", appt_type)
        ).fetchone()
        
        max_capacity = rule_row[0] if rule_row else 5
        
        # Count existing scheduled/checked-in
        existing = conn.execute(
            """SELECT COUNT(*) FROM core_appointment 
               WHERE appt_date = ? AND appt_time LIKE ? AND appt_type = ? AND status != 'Cancelled'""",
            (date_str, f"{time_str}%", appt_type)
        ).fetchone()[0]
        
        conn.close()
        
        return json_response({
            "existing": existing,
            "max_capacity": max_capacity,
            "at_capacity": existing >= max_capacity,
            "remaining": max(0, max_capacity - existing)
        })
    except Exception as e:
        return json_response({"error": str(e)}, status_code=500)

# ─── 6. Check-In Endpoint ────────────────────────────────────────────────────
@app.route(route="check-in", methods=["POST"])
def check_in(req: func.HttpRequest) -> func.HttpResponse:
    conn = get_db_connection()
    try:
        body = req.get_json()
        appt_id = body.get("appointment_id")
        visitor_name = body.get("visitor_name", "")
        trailer_no = body.get("trailer_no", "")
        drivers_license_state = body.get("drivers_license_state", "")
        load_lock = body.get("load_lock", "")
        assigned_door_id = body.get("assigned_door_id")
        pit_operator_id = body.get("pit_operator_id")
        notes = body.get("notes", "")
        
        if not appt_id:
            return json_response({"error": "Missing appointment_id"}, status_code=400)
            
        # Get appointment details to calculate check-in status (Early/On Time/Late)
        appt = conn.execute("SELECT scheduled_datetime FROM core_appointment WHERE id = ?", (appt_id,)).fetchone()
        if not appt:
            return json_response({"error": "Appointment not found"}, status_code=404)
            
        check_in_time = datetime.datetime.utcnow()
        check_in_time_str = check_in_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        
        # Calculate status
        scheduled_dt = datetime.datetime.strptime(appt["scheduled_datetime"].split(".")[0], "%Y-%m-%d %H:%M:%S")
        diff = (check_in_time - scheduled_dt).total_seconds() / 60.0
        
        if diff < -15:
            new_status = 'Early'
        elif -15 <= diff <= 15:
            new_status = 'On Time'
        else:
            new_status = 'Late'
            
        # Insert DriverVisit record
        conn.execute(
            """INSERT INTO core_drivervisit 
               (visitor_name, trailer_no, drivers_license_state, load_lock, check_in_time, check_out_time, in_out_status, notes, appointment_id, assigned_door_id, pit_operator_id)
               VALUES (?, ?, ?, ?, ?, NULL, 'In', ?, ?, ?, ?)""",
            (visitor_name, trailer_no, drivers_license_state, load_lock, check_in_time_str, notes, appt_id, assigned_door_id, pit_operator_id)
        )
        
        # Update Appointment status
        conn.execute(
            "UPDATE core_appointment SET status = ? WHERE id = ?",
            (new_status, appt_id)
        )
        
        # Update Door status to Occupied
        if assigned_door_id:
            conn.execute(
                "UPDATE core_door SET status = 'Occupied' WHERE id = ?",
                (assigned_door_id,)
            )
            
        conn.commit()
        conn.close()
        return json_response({"success": True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return json_response({"error": str(e)}, status_code=500)

# ─── 7. Check-Out Endpoint ───────────────────────────────────────────────────
@app.route(route="check-out", methods=["POST"])
def check_out(req: func.HttpRequest) -> func.HttpResponse:
    conn = get_db_connection()
    try:
        body = req.get_json()
        appt_id = body.get("appointment_id")
        notes = body.get("notes", "")
        
        if not appt_id:
            return json_response({"error": "Missing appointment_id"}, status_code=400)
            
        # Find driver visit matching checked-in appointment
        visit = conn.execute(
            "SELECT id, check_in_time, assigned_door_id FROM core_drivervisit WHERE appointment_id = ? AND in_out_status = 'In'", 
            (appt_id,)
        ).fetchone()
        
        if not visit:
            return json_response({"error": "Active driver visit not found"}, status_code=404)
            
        check_out_time = datetime.datetime.utcnow()
        check_out_time_str = check_out_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        
        # Dwell time calculation
        check_in_dt = datetime.datetime.strptime(visit["check_in_time"].split(".")[0], "%Y-%m-%d %H:%M:%S")
        dwell_seconds = int((check_out_time - check_in_dt).total_seconds())
        
        # Update DriverVisit record
        conn.execute(
            """UPDATE core_drivervisit 
               SET check_out_time = ?, dwell_seconds = ?, in_out_status = 'Out', notes = COALESCE(notes || '\n' || ?, ?)
               WHERE id = ?""",
            (check_out_time_str, dwell_seconds, notes, notes, visit["id"])
        )
        
        # Update Appointment status to Completed
        conn.execute(
            "UPDATE core_appointment SET status = 'Completed' WHERE id = ?",
            (appt_id,)
        )
        
        # Free up assigned door
        if visit["assigned_door_id"]:
            conn.execute(
                "UPDATE core_door SET status = 'Open' WHERE id = ?",
                (visit["assigned_door_id"],)
            )
            
        conn.commit()
        conn.close()
        return json_response({"success": True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return json_response({"error": str(e)}, status_code=500)

# ─── 8. KPI Export Endpoint ──────────────────────────────────────────────────
EXPORT_COLUMNS = [
    "Appt_Type", "In", "Out", "Appt_Time", "Status", "Customer", "Type", "Carrier",
    "BOL-Shipment_No", "Visitor_Name", "Delivery_No", "Trailer_No", "Drivers_License_State",
    "Load_Lock", "Assigned_Door", "Dwell_Time", "Notes", "PIT_Operator", "InOutStatus",
    "Color_Coding", "Appt_Day", "Appt_Slot", "Appt_Month", "Appt_Year"
]

@app.route(route="kpi-export", methods=["GET"])
def kpi_export(req: func.HttpRequest) -> func.HttpResponse:
    try:
        date_from = req.params.get("date_from", "")
        date_to = req.params.get("date_to", "")
        appt_type = req.params.get("appt_type", "All")
        status = req.params.get("status", "All")
        fmt = req.params.get("format", "json")
        
        include_scheduled = req.params.get("include_scheduled") == "true"
        include_checked_in = req.params.get("include_checked_in") == "true"
        include_completed = req.params.get("include_completed") == "true"

        conn = get_db_connection()
        
        sql = """
            SELECT a.*, 
                   cust.name as customer, 
                   carr.name as carrier, 
                   pt.name as product_type,
                   v.visitor_name, v.trailer_no, v.check_in_time, v.check_out_time, v.dwell_seconds, v.load_lock, v.in_out_status, v.notes as visit_notes,
                   d.door_name, op.name as pit_operator
            FROM core_appointment a
            LEFT JOIN core_customer cust ON a.customer_id = cust.id
            LEFT JOIN core_carrier carr ON a.carrier_id = carr.id
            LEFT JOIN core_producttype pt ON a.product_type_id = pt.id
            LEFT JOIN core_drivervisit v ON a.id = v.appointment_id
            LEFT JOIN core_door d ON v.assigned_door_id = d.id
            LEFT JOIN core_pitoperator op ON v.pit_operator_id = op.id
            WHERE a.appt_date >= ? AND a.appt_date <= ?
        """
        params = [date_from, date_to]
        
        if appt_type != "All":
            sql += " AND a.appt_type = ?"
            params.append(appt_type)
            
        if status != "All":
            sql += " AND a.status = ?"
            params.append(status)
            
        # Build status array filter based on checkboxes
        status_filters = []
        if include_scheduled:
            status_filters.append("'Scheduled'")
        if include_checked_in:
            status_filters.extend(["'Checked In'", "'Early'", "'On Time'", "'Late'"])
        if include_completed:
            status_filters.append("'Completed'")
            
        if status_filters:
            sql += f" AND a.status IN ({','.join(status_filters)})"
        else:
            sql += " AND 1=0" # returns empty if none checked
            
        sql += " ORDER BY a.scheduled_datetime ASC"
        
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        
        export_rows = []
        for r in rows:
            # 1. Format datetime values
            def fmt_dt(dt_str):
                if not dt_str: return ""
                try:
                    dt = datetime.datetime.strptime(dt_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                    # Excel expects format: M/D/YYYY H:MM AM/PM
                    return dt.strftime("%m/%d/%Y %I:%M %p").replace(" 0", " ")
                except:
                    return dt_str

            check_in_time = fmt_dt(r["check_in_time"])
            check_out_time = fmt_dt(r["check_out_time"])
            appt_time = fmt_dt(r["scheduled_datetime"])
            
            # Dwell time format
            dwell_display = ""
            if r["dwell_seconds"] is not None:
                h, remainder = divmod(r["dwell_seconds"], 3600)
                m, s = divmod(remainder, 60)
                dwell_display = f"{h:02d}:{m:02d}:{s:02d}"
                
            # Excel fraction slot logic
            time_slot_fraction = ""
            if r["appt_time"]:
                try:
                    t_parts = r["appt_time"].split(":")
                    h_val = int(t_parts[0])
                    m_val = int(t_parts[1])
                    time_slot_fraction = round((h_val * 60 + m_val) / 1440.0, 4)
                except:
                    pass
                    
            appt_date_obj = datetime.datetime.strptime(r["appt_date"], "%Y-%m-%d")
            
            export_row = [
                r["appt_type"],
                check_in_time,
                check_out_time,
                appt_time,
                r["status"],
                r["customer"],
                r["product_type"],
                r["carrier"],
                r["bol_shipment_no"],
                r["visitor_name"] or "",
                r["delivery_no"] or "",
                r["trailer_no"] or "",
                "", # Drivers license state column placeholder or actual val
                r["load_lock"] or "",
                r["door_name"] or "",
                dwell_display,
                r["visit_notes"] or r["notes"] or "",
                r["pit_operator"] or "",
                r["in_out_status"] or "",
                "", # Color coding placeholder
                appt_date_obj.strftime("%A"),
                time_slot_fraction,
                appt_date_obj.strftime("%B"),
                appt_date_obj.year
            ]
            export_rows.append(export_row)
            
        if fmt == "tsv":
            # Output tab-separated format for clipboard pasting
            tsv_data = "\n".join(["\t".join(map(str, row)) for row in export_rows])
            return json_response({"tsv": tsv_data})
            
        elif fmt == "csv":
            # Output standard CSV text format for file downloads
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(EXPORT_COLUMNS)
            writer.writerows(export_rows)
            return func.HttpResponse(
                body=output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=kpi_export.csv"}
            )
            
        else: # default json
            return json_response({
                "columns": EXPORT_COLUMNS,
                "rows": export_rows
            })
            
    except Exception as e:
        return json_response({"error": str(e)}, status_code=500)
